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
import os


CONNECTION_STRING = "mongodb+srv://DuuuKieee:899767147@loginserver.hqnkiia.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(CONNECTION_STRING)
dbname = "CryptoProject"
db = client[dbname]
file_collection = db["fs.files"]
user_collection = db["UserCollection"]
account =""
def main():
    # Connect to MongoDB
    print("/publish: to publish file if you are admin!")
    print("/verify: verify the file you have!")
    print("/download: download file by name")
    print("/search: search a file with name or date (example: 22/6/2023)")
    
    global account 
    print("Account:")
    account = input()
    list_files()
    print ("Command:")
    command = input()

    if(command == "/publish"):
        PublisherPermission()
    elif(command == "/verify"):
        RecepientPermission()
    elif(command=="/download"):
        download_file()
    elif(command=="/benchmark"):
        bench_mark()
    elif(command =="/search"):
        search()
    print("---------------------------")
    return main()
    # Generate keys
def makeWatermark():
    watermarkName = "qr.pdf"
    doc = canvas.Canvas(watermarkName)
    qr = QRCodeImage(
        size=30 * mm,
        fill_color='black',
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
    qr.drawOn(doc, 20 * mm, 40 * mm)
    doc.save()
    return watermarkName

def makePdf(src, watermark):
    merged = src + "_signed.pdf"
    with open(src, "rb") as input_file, open(watermark, "rb") as watermark_file:
        input_pdf = PdfReader(input_file)
        watermark_pdf = PdfReader(watermark_file)
        watermark_page = watermark_pdf.pages[0]
        output = PdfWriter()

        for i in range(len(input_pdf.pages)):
            if(i==0):
                pdf_page = input_pdf.pages[i]
                pdf_page.merge_page(watermark_page)
                output.add_page(pdf_page)
            else:
                pdf_page = input_pdf.pages[i]
                output.add_page(pdf_page)
                

        with open(merged, "wb") as merged_file:
            output.write(merged_file)
        return merged
def PublisherPermission():
    try:
        doccument = user_collection.find_one({"username": account})
  
        if(doccument["role"] == "0"):
            pk, sk = Dilithium3.keygen()
            print("File path:") 
            path =input()
            print("File name:")
            file_name = input()
            print("Waiting for publish...")
            path = makePdf(path, makeWatermark())
            with open(path, "rb") as file:
                pdf_file = file.read()
            sig = Dilithium3.sign(sk, pdf_file)
            pkh_ex = binascii.hexlify(pk).decode('utf-8')
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y")

            # Upload signature to MongoDB

            fs = gridfs.GridFS(file_collection.database)
            with open(path, "ab") as f:
                f.write(sig)
            with open(path, "rb") as file:
                pdf_file = file.read()
            file_id = fs.put(pdf_file, filename = file_name, publisher = account,Date = dt_string, publickey = pkh_ex )
            with open(file_name+"_signed.pdf", "wb") as f:
                f.write(pdf_file)
            print("Published!")
        else:
            print("You do not have permission to do that.")
        
    except Exception as e: 
        print(e)
        print("Duong dan khong hop le")
        PublisherPermission()
    

def RecepientPermission():
    print("File path:")
    path = input()
    flag = 0
    try:
        for document in file_collection.find():
            public_key = binascii.unhexlify(document["publickey"])
            with open(path, "rb") as file:
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0, os.SEEK_SET)
                pdf_file = file.read(file_size - 3293)
                file.seek(-3293, 2)  
                signature = file.read()  
            verify = Dilithium3.verify(public_key, pdf_file, signature)
            if(verify == True):
                print(f"Verification result for signature {document['_id']}: {verify}")
                flag = 0
                break
            else:
                flag+=1
        if(flag != 0):
            print("Verification result for signature: FALSE")
             
    except Exception as e: 
        print(e)
        print("File khong hop le")
        RecepientPermission(file_collection)

def download_file():
    global account
    print("Enter file name to download: ")
    file_name = input()
    fs = gridfs.GridFS(file_collection.database)
    user = user_collection.find_one({"username": account })
    file = fs.find_one({"filename": file_name})

    if file:
        with open(file_name+"signed.pdf", "wb") as f:
            f.write(file.read())
        print("Downloaded successfully!")
    else:
        print("File not found!")
        download_file()

def list_files():
    print("Available files:")
    for i, document in enumerate(file_collection.find(), 1):
        file_name = document["filename"]
        file_date = document["uploadDate"]
        print(f"{i}: {file_name} (Uploaded on: {file_date})")

def search():
    print("Enter a keyword to search for: ")
    query = input()
    pipeline = [
        {
            "$search": {
                "index": "Searching",
                "text": {
                    "query": query,
                    "path": {
                        "wildcard": "*",
                    }
                    
                }
                
            
            }
        },
        {
            "$project": {
                "_id": 0,
                "filename": 1,
                "Date": 1
            }
        }              
]
    
    results = file_collection.aggregate(pipeline)
    for i, doc in enumerate(list(results), start=1):
        print(f"{i}: {doc}")

def bench_mark(path = input()):
    count = 10
    with open(path, "rb") as file:
            pdf_file = file.read()
    benchmark_dilithium(Dilithium3,"Dilithium3",count,pdf_file)

def Login(username):
    global account
    account = username
    
    
if __name__ == "__main__":
    main()