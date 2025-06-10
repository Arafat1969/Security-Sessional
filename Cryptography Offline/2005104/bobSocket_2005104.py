import aes_2005104 as aes
import ecdh_2005104 as ecdh
import socket

host = '127.0.0.1'
port = 12345

def initECDH(P, a, b, G, k=128): 
    bobPrivate = ecdh.generatePrivateKey(k, P)
    bobPublic = ecdh.generatePublicKey(bobPrivate, G, a, P)
    
    return bobPublic, bobPrivate

def calculateSharedKey(privateKey, alicePublic, a, p):
    sharedPoint = ecdh.computeShareKey(privateKey, alicePublic, a, p)
    sharedSecret = sharedPoint[0]
    
    return sharedSecret

def keySchedule(sharedKey):
    keyString = ""
    for i in range(16):
        byte_val = (sharedKey >> (8 * i)) & 0xFF
        keyString += chr(byte_val)
    
    keyMatrix = aes.createKeyMatrix(keyString)
    roundKeys = aes.generateKeyMatrices(keyMatrix)
    
    return roundKeys

def encrypt(message, roundKeys):
    textBlocks = aes.generateTextBlocks(message)
    stateMatrices = aes.generateStateMatrices(textBlocks)
    iv, cipherTextMatrices = aes.generateCipherTexts(stateMatrices, roundKeys)


    print("Bob's Cipher Text in ASCII: ", end="")
    cipherStr = aes.printMatricesToAscii(cipherTextMatrices)
    cipherText = iv + cipherStr
    return cipherText

def decrypt(cipherText, roundKeys):
    iv = cipherText[:16]
    cipherTextBlocks = cipherText[16:]
    
    blocks = []
    for i in range(0, len(cipherTextBlocks), 16):
        blocks.append(cipherTextBlocks[i:i+16])

    cipherMatrices = aes.generateStateMatrices(blocks)
    decipheredMatrices = aes.generateDecipherText(cipherMatrices, roundKeys, iv)
    
    decipheredText = aes.printMatricesToAscii(decipheredMatrices)
    
    try:
        plainText = aes.removePadding(decipheredText)
    except ValueError:
        plainText = decipheredText
    
    return plainText

def main():
    print("BOB (SERVER)")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    
    print(f"Server started on {host}:{port}")
    print("Waiting for ALICE to connect...")
    
    client, addr = server.accept()
    print(f"\nALICE connected from {addr}")
    
    paramsLength = int(client.recv(1024).decode())
    
    paramsStr = client.recv(paramsLength).decode()
    params = paramsStr.split()
    
    P = int(params[0])
    a = int(params[1])
    b = int(params[2])
    G = (int(params[3]), int(params[4]))
    alicePublic = (int(params[5]), int(params[6]))
    
    print("\nReceived ECDH parameters from ALICE:")
    # print("P = ",P)
    # print("a = ",a)
    # print("b = ",b)
    # print("G = ",G)
    print("Alice's public key = ",alicePublic)
    
    print("\nGenerating key pair...")
    bobPublic, bobPrivate = initECDH(P, a, b, G)
    print(f"Bob's private key = ",bobPrivate)
    print(f"Bob's public key = ",bobPublic)
    
    bobPublicStr = f"{bobPublic[0]} {bobPublic[1]}"
    client.sendall(bobPublicStr.encode())
    
    sharedKey = calculateSharedKey(bobPrivate, alicePublic, a, P)
    print("Shared secret (x-coordinate): ",sharedKey)
    
    print("Generating AES round keys...")
    roundKeys = keySchedule(sharedKey)
    
    print("\nSecure communication established!")
    print("Type 'end' to terminate the conversation.")
    
    while True:
        receivedCipher = client.recv(4096).decode('latin-1') 
        print(f"Received encrypted message: ",receivedCipher)
        
        plainText = decrypt(receivedCipher, roundKeys)
        print(f"Alice: {plainText}")
        
        if plainText.lower() == 'end':
            break
        
        message = input("Bob: ")
        cipherText = encrypt(message, roundKeys)
        print("Sending encrypted message: ",cipherText)
        client.sendall(cipherText.encode('latin-1')) 
        
        if message.lower() == 'end':
            break
    

    print("\nClosing connection...")
    client.close()
    server.close()
    print("Connection closed.")

if __name__ == "__main__":
    main()