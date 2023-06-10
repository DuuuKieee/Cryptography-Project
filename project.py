import binascii
import gridfs
from dilithium import Dilithium3
from pymongo import MongoClient
from benchmark_dilithium import benchmark_dilithium
def main():
    # Connect to MongoDB
    print("Account:")
    account = input()
    CONNECTION_STRING = "mongodb+srv://DuuuKieee:899767147@loginserver.hqnkiia.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(CONNECTION_STRING)
    dbname = "CryptoProject"
    db = client[dbname]
    signature_collection = db["SignatureCollection"]
    file_collection = db["fs.files"]
    print ("Command:")
    command = input()

    if(command == "/help"):
        print("/publish: to publish file if you are admin!")
        print("/verify: verify the file you have!")
        print("/download: download file by name")
        return main()
    
    if(account == "admin"):
        if(command == "/publish"):
            PublisherPermission(signature_collection)
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
def PublisherPermission(collection):
    try:
        pk, sk = Dilithium3.keygen()
        # Load PDF file to sign
        print("File path:")
        path =input()
        print("File name:")
        file_name = input()
        fs = gridfs.GridFS(collection.database)
    
        with open(path, "rb") as file:
            pdf_file = file.read()
            file_id = fs.put(pdf_file, filename = file_name)
        sig = Dilithium3.sign(sk, pdf_file)
        sig_hex = binascii.hexlify(sig).decode('utf-8')
        collection.insert_one({
        "signature": sig_hex,
        "public_key": binascii.hexlify(pk).decode('utf-8')
    })
        print("Published!")
    except:
        print("Duong dan khong hop le")
        PublisherPermission(collection)

    #     # Upload signature to MongoDB

def RecepientPermission(collection):
    print("File path:")
    path = input()
    
    flag = 0
    try:
        for document in collection.find():
            signature = binascii.unhexlify(document["signature"])
            public_key = binascii.unhexlify(document["public_key"])
            with open(path, "rb") as file:
                pdf_file = file.read()
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