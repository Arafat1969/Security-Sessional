import aes_2005104 as aes
import ecdh_2005104 as ecdh
import socket

host= '127.0.0.1'
port = 12345

def initECDH(k=128): 
    P, a, b, G = ecdh.generateEcdhParameters(k)
    alicePrivate = ecdh.generatePrivateKey(k, P)
    alicePublic = ecdh.generatePublicKey(alicePrivate, G, a, P)
    return P, a, b, G, alicePublic, alicePrivate

def calculateSharedKey(privateKey, bobPublic, a, p):
    sharedPoint = ecdh.computeShareKey(privateKey, bobPublic, a, p)
    sharedSecret = sharedPoint[0]
    return sharedSecret

def keySchedule(sharedKey):
    keyString = ""
    for i in range(16):
        byteVal = (sharedKey >> (8 * i)) & 0xFF
        keyString += chr(byteVal)
    
    keyMatrix = aes.createKeyMatrix(keyString)
    
    roundKeys = aes.generateKeyMatrices(keyMatrix)
    
    return roundKeys

def encrypt(message, roundKeys):    
    textBlocks = aes.generateTextBlocks(message)
    stateMatrices = aes.generateStateMatrices(textBlocks)
    
    iv, cipherTextMatrices = aes.generateCipherTexts(stateMatrices, roundKeys)
    
    print("Alice's Cipher Text in ASCII: ", end="")
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
    print("ALICE (CLIENT)")
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    client.connect((host, port))
    
    print("Connected to BOB (server).")
    
    P, a, b, G, alicePublic, alicePrivate = initECDH()
    
    params = f"{P} {a} {b} {G[0]} {G[1]} {alicePublic[0]} {alicePublic[1]}"
    
    print("\nSending ECDH parameters to BOB...")
    client.sendall(str(len(params)).encode())
    client.sendall(params.encode())
    

    bobPublicStr = client.recv(1024).decode().split()
    bobPublic = (int(bobPublicStr[0]), int(bobPublicStr[1]))
    print("Received BOB's public key: ",{bobPublic})
    

    sharedKey = calculateSharedKey(alicePrivate, bobPublic, a, P)
    print("Shared secret (x-coordinate): ",sharedKey)
    
    print("Generating AES round keys...")
    roundKeys = keySchedule(sharedKey)
    
    print("\nSecure communication established!")
    print("Type 'end' to terminate the conversation.")
    print("-" * 50)
    
    while True:
        message = input("Alice: ")
        
        cipherText = encrypt(message, roundKeys)
        # print("Sending encrypted message: ",len(cipherText)," bytes)")
        print("Sending encrypted message: ",cipherText)
        client.sendall(cipherText.encode('latin-1'))
        
        
        if message.lower() == 'end':
            break
        
        receivedCipher = client.recv(4096).decode('latin-1')
        # print("Received encrypted message: ",len(receivedCipher), " bytes")
        print("Received encrypted message: ",receivedCipher)
        
        plainText = decrypt(receivedCipher, roundKeys)
        print("Bob: ",plainText)
        
        if plainText.lower() == 'end':
            break
        
    print("\nClosing connection...")
    client.close()
    print("Connection closed.")

if __name__ == "__main__":
    main()