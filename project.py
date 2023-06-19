import binascii
import gridfs
from datetime import datetime
from dilithium import Dilithium3
from pymongo import MongoClient
import qrcode
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab_qrcode import QRCodeImage
from benchmark_dilithium import benchmark_dilithium
from reportlab.platypus import Paragraph, SimpleDocTemplate
from PyPDF2 import PdfReader, PdfWriter



CONNECTION_STRING = "mongodb+srv://DuuuKieee:899767147@loginserver.hqnkiia.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(CONNECTION_STRING)
dbname = "CryptoProject"
db = client[dbname]
signature_collection = db["SignatureCollection"]
file_collection = db["fs.files"]
account = "test"
def main():
    # Connect to MongoDB
    global account 
    print("Account:")
    account = input()
    print ("Command:")
    command = input()

    if(command == "/help"):
        print("/publish: to publish file if you are admin!")
        print("/verify: verify the file you have!")
        print("/download: download file by name")
        return main()
    
    if(account == "admin"):
        if(command == "/publish"):
            PublisherPermission()
        elif(command == "/verify"):
            RecepientPermission(signature_collection)
        elif(command=="/download"):
            download_file(file_collection)
        elif(command=="/benchmark"):
            # print("Số lần gọi thuật toán để đo hiệu suất:")
            # count = input()
            print("File path:")
            path = input()
            bench_mark(path)
        else: 
            print("Command not found for admin!")
    else:
        if(command =="/publish"):
            print("Permission denied")
        elif(command=="/verify"):
            RecepientPermission(signature_collection)
        elif(command=="/download"):
            download_file(file_collection)
        else: 
            print("Command not found for client!") 
    print("---------------------------")
    return main()
    # Generate keys
def makeWatermark():
    watermarkName = "qr.pdf"
    doc = canvas.Canvas(watermarkName)
    qr = QRCodeImage(
        size=25 * mm,
        fill_color='blue',
        back_color=(0, 0, 0, 0),
        border=4,
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    )
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    qr.add_data("Signed by: "+account+ "\n"+"Day/time: "+ dt_string)
    # qr.add_data(account+ "\n")
    # qr.make(fit=True)
    qr.drawOn(doc, 30 * mm, 50 * mm)
    doc.save()
    return watermarkName

def makePdf(src, watermark):
    merged = src + "_signed.pdf"
    with open(src, "rb") as input_file, open(watermark, "rb") as watermark_file:
        input_pdf = PdfReader(input_file)
        watermark_pdf = PdfReader(watermark_file)
        watermark_page = watermark_pdf.pages[0]
        output = PdfWriter()

        pdf_page = input_pdf.pages[0]
        pdf_page.merge_page(watermark_page)
        output.add_page(pdf_page)

        with open(merged, "wb") as merged_file:
            output.write(merged_file)
        return merged
def PublisherPermission():
    try:
        global account
        pk, sk = Dilithium3.keygen()
        print("File path:") 
        path =input()
        print("File name:")
        file_name = input()
        path = makePdf(path, makeWatermark())
        with open(path, "rb") as file:
            pdf_file = file.read()
        sig = Dilithium3.sign(sk, pdf_file)

        fs = gridfs.GridFS(signature_collection.database)
        with open(path, "ab") as f:
            f.write(sig)
            
        fs = gridfs.GridFS(signature_collection.database)
        with open(path, "rb") as file:
            file_id = fs.put(pdf_file, filename = file_name, publisher = account, publickey = pk )
        sig_hex = binascii.hexlify(sig).decode('utf-8')
        pkh_ex = binascii.hexlify(pk).decode('utf-8')
        with open(path, "rb") as f:
            f.seek(-3293, 2)  # Đặt con trỏ đọc tại vị trí cần đọc
            last_bytes = f.read()  # Đọc 3,293 byte cuối
        with open('signed.pdf', "wb") as f:
            f.write(pdf_file)
        signature_collection.insert_one({
        "signature": sig_hex,
        "public_key": binascii.hexlify(pk).decode('utf-8')
        })
    
        print("Published!")
    except Exception as e: 
        print(e)
        print("Duong dan khong hop le")
        PublisherPermission()
    #     # Upload signature to MongoDB

def RecepientPermission(collection):
    print("File path:")
    path = input()
    
    flag = 0
    try:
        for document in file_collection.find():
            signature = binascii.unhexlify(document["signature"])
            public_key = binascii.unhexlify(document["public_key"])
            with open(path, "rb") as file:
                pdf_file = file.read()
                file.seek(-3293, 2)  # Đặt con trỏ đọc tại vị trí cần đọc
                signature = file.read()  # Đọc 3,293 byte cuối
            verify = Dilithium3.verify(public_key, pdf_file, signature)
            if(verify == True):
                print(f"Verification result for signature {document['_id']}: {verify}")
                flag = 0
                break
            else:
                flag+=1
        if(flag != 0):
            print("false")
             
    except:
        print("File khong hop le")
        RecepientPermission(collection)

def download_file(collection):
    list_files(collection)
    print("File name:")
    file_name = input()
    fs = gridfs.GridFS(collection.database)
    file = fs.find_one({"filename": file_name})

    if file:
        with open(file_name+".pdf", "wb") as f:
            f.write(file.read())
        print("Downloaded successfully!")
    else:
        print("File not found!")
        download_file(collection)

def list_files(collection):
    print("Available files:")
    for i, document in enumerate(collection.find(), 1):
        file_name = document["filename"]
        file_date = document["uploadDate"]
        print(f"{i}: {file_name} (Uploaded on: {file_date})")

def bench_mark(path):
    count = 10
    with open(path, "rb") as file:
            pdf_file = file.read()
    benchmark_dilithium(Dilithium3,"Dilithium3",count,pdf_file)
    
if __name__ == "__main__":
    main()