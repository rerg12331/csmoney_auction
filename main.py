import requests
import json 
import time 
import sqlite3
from collections import Counter

headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
         'Content-Type':'application/json; charset=utf-8'}

def create_database():
    # Создаем подключение к базе данных (файл my_database.db будет создан)
    db = sqlite3.connect('my_database.db')
    sql = db.cursor()
    
    # Создаем таблицу, если она не существует
    sql.execute('''CREATE TABLE IF NOT EXISTS Users (
        id TEXT
    )''')
    db.commit()
    sql.execute("SELECT COUNT(*) id FROM Users")
    print(sql.fetchall())  

def main(db,sql):
    r = requests.get('https://cs.money/1.0/auction/lots?appId=730&limit=200&offset=0&order=desc&sort=betsAmount&status=running', headers=headers)
    response = json.loads(r.text)
    for i in response:
        if i == 'error':
            print('error')
            time.sleep(200)
            continue
        else:
            sql.execute("SELECT id FROM Users WHERE id=?", (i['id'],))
            if sql.fetchone() is None:
                sql.execute("INSERT INTO Users VALUES (?)", (i['id'],))
                db.commit()
                total_sum = 0
                stickersfull = []
                overpay = i['overpay']
                if overpay is not None:
                    if "float" in overpay and "stickers" in overpay:
                        total_sum = overpay["float"] + overpay["stickers"]
                    elif "float" in overpay:
                        total_sum = overpay["float"]
                    elif "stickers" in overpay:
                        total_sum = overpay["stickers"]

                if i['stickers'] is not None:
                    stickersfull = [{stick['name']: stick['price'], 'Wear': stick['wear']} for stick in i['stickers'] if stick is not None and i['stickers'] is not None]            
                
                countpricestickers = [total for x in stickersfull for total in x.values()][::2]
                total = sum(countpricestickers)
                c = Counter(countpricestickers)
                count = [c[x] for x in countpricestickers if c[x]>=3]
                
                r = total
                if len(count) == 3:
                    r = total*1.15
                elif len(count) == 4:
                    r = total*1.25
                else:
                    pass

                if r>=4 and r >= i['price']*1.10 or total_sum>1.2:    
                    gun = {
                        'Name':i['fullName'],
                        'Float':i['float'],
                        'Price':i['price'],
                        'Def-price':i['price']-total_sum,
                        'Stickers':stickersfull,
                        'Total-price-stickers':total,
                        'overpay':total_sum,
                        'Img':i['preview'],
                    }
                    telegram_bot(item=gun)
                    print(gun)

def telegram_bot(item):
    TOKEN = "your token"
    channel_id = 'your id'
    
    Name = item['Name']
    price = item['Price']
    def_price = item['Def-price']
    Float = item['Float']
    total_price_stickers = item['Total-price-stickers']
    overpay = item['overpay']
    Img = item['Img']
    info = float("{0:.2f}".format(price/1.2186))
    message = f"CS.MONEY(auction)\n\n<b>Name</b>: <code>{Name}</code>\n<b>Float</b>: {Float}\n\n<b>Price</b>: <strong>{price}</strong>$\n<b>def_Price</b>: <strong>{def_price}</strong>$\n\n<b>Stickers</b>:\n"
    # Добавляем информацию о стикерах
    stickers = item.get('Stickers', [])
    if stickers:
        for i, sticker in enumerate(stickers, 1):
            name = next(iter(sticker.keys()))
            price = next(iter(sticker.values()))
            wear = sticker['Wear']
            message += f"{i}. <code>{name}</code>| {price}$\nWear = {wear}\n"
    else:
        message += "No stickers available\n"
    # Добавляем информацию о общей стоимости стикеров
    message += f"\nℹ️<b>Total_price_stickers</b>: {total_price_stickers}$\n"
    message += f'<b>Overpay</b>: <strong>{overpay}</strong>$\n<b>Inventory price if you buy this item</b>:<strong>{info}</strong>$'
    
    data2 = {
            "parse_mode": "HTML"    
            }
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    data1 = {
           "chat_id": channel_id,
           "photo": Img,
           "caption": message,
           "parse_mode": "HTML"    
        }
    response = requests.post(url,data=data1)

    if response.status_code != 200:
        print(Name,"Ошибка при отправке сообщения в канал",response.text)
        message +='\n<b>Не удалось загрузить фотографию!</b>'
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={channel_id}&text={message}",data=data2)

if __name__ == '__main__':
    db = sqlite3.connect('my_database.db')
    sql = db.cursor()
    create_database()
    main(db,sql)
    while True:
        try:
            main(db,sql)
            time.sleep(15)
        except Exception as e:
           print(f'Произошла ошибка! {e}')
           time.sleep(15)