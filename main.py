from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from web3 import Web3
import requests
from collections import defaultdict

app = FastAPI()

# LINKS
POLYGONSCAN_API_KEY = "WKBWY2X3MSRSSVTRMWX61YWXJG5MWETKH2"
POLYGON_RPC = "https://polygon-mainnet.infura.io/v3/87ed9399cc8540408eae46546f782e28"  # добавлен Infura формат
TOKEN_ADDRESS = Web3.to_checksum_address("0x1a9b54a3075119f1546c52ca0940551a6ce5d2d0")


web3 = Web3(Web3.HTTPProvider(POLYGON_RPC))

# Получить ABI токена через Polygonscan
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
]

# Контракт
contract = web3.eth.contract(address=TOKEN_ADDRESS, abi=ERC20_ABI)

decimals = contract.functions.decimals().call()

def format_balance(balance_raw):
    return balance_raw / (10 ** decimals)

class AddressList(BaseModel):
    addresses: List[str]

@app.get("/get_balance")
def get_balance(address: str):
    try:
        address = Web3.to_checksum_address(address)
        balance = contract.functions.balanceOf(address).call()
        return {"balance": format_balance(balance)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/get_balance_batch")
def get_balance_batch(data: AddressList):
    try:
        results = []
        for addr in data.addresses:
            address = Web3.to_checksum_address(addr)
            bal = contract.functions.balanceOf(address).call()
            results.append(format_balance(bal))
        return {"balances": results}
    except Exception as e:
        return {"error": str(e)}

@app.get("/get_token_info")
def get_token_info():
    try:
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        total = contract.functions.totalSupply().call()
        return {
            "name": name,
            "symbol": symbol,
            "totalSupply": format_balance(total)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/get_top")
def get_top(n: int = 10):
    try:
        url = "https://api.polygonscan.com/api"
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": TOKEN_ADDRESS,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
            "apikey": POLYGONSCAN_API_KEY
        }
        response = requests.get(url, params=params).json()

        if response["status"] != "1":
            return {"error": response.get("result", "No data")}

        txs = response["result"]

        balances = defaultdict(int)

        for tx in txs:
            from_addr = tx["from"]
            to_addr = tx["to"]
            value = int(tx["value"])
            balances[from_addr] -= value
            balances[to_addr] += value

        # Удалим адреса с нулевым балансом
        non_zero = {addr: bal for addr, bal in balances.items() if bal > 0}

        # Сортировка по балансу
        top = sorted(non_zero.items(), key=lambda x: x[1], reverse=True)[:n]

        # Форматируем
        formatted = [(addr, format_balance(bal)) for addr, bal in top]

        return {"top": formatted}

    except Exception as e:
        return {"error": str(e)}
@app.get("/get_top_with_transactions")
def get_top_with_transactions(n: int = 10):
    try:
        url = "https://api.polygonscan.com/api"
        tx_params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": TOKEN_ADDRESS,
            "page": 1,
            "offset": 100,  # можно увеличить, чтобы больше уникальных адресов
            "sort": "desc",
            "apikey": POLYGONSCAN_API_KEY
        }
        tx_response = requests.get(url, params=tx_params).json()

        if tx_response["status"] != "1":
            return {"error": tx_response.get("result", "Ошибка получения транзакций")}

        from collections import defaultdict
        from datetime import datetime

        txs = tx_response["result"]
        address_last_tx = {}
        address_set = set()

        for tx in txs:
            addr = tx["to"]
            ts = int(tx["timeStamp"])
            if addr not in address_last_tx:
                address_last_tx[addr] = ts
            address_set.add(addr)

        # получаем балансы
        balances = []
        for addr in address_set:
            try:
                balance = contract.functions.balanceOf(Web3.to_checksum_address(addr)).call()
                if balance > 0:
                    last_tx_time = datetime.utcfromtimestamp(address_last_tx[addr]).strftime('%Y-%m-%d %H:%M:%S')
                    balances.append((addr, format_balance(balance), last_tx_time))
            except:
                continue

        # сортировка по балансу и ограничение по N
        balances = sorted(balances, key=lambda x: x[1], reverse=True)[:n]
        return {"top_with_tx": balances}

    except Exception as e:
        return {"error": str(e)}
