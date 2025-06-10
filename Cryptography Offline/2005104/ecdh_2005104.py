import random
import sympy
import time

def legendreSymbol(a, p):
    
    if a % p == 0:
        return 0
    
    ls = pow(a, (p - 1) // 2, p)
    
    if ls == p - 1:
        return -1
    return ls

def tonelliShanks(n, p):
    
    if legendreSymbol(n, p) != 1:
        return None 
    
    if p % 4 == 3:
        return pow(n, (p + 1) // 4, p)
    
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1
    
    z = 2
    while legendreSymbol(z, p) != -1:
        z += 1
    
    m = s
    c = pow(z, q, p)
    t = pow(n, q, p)
    r = pow(n, (q + 1) // 2, p)

    while t != 1:
        i = 0
        temp = t
        while temp != 1 and i < m - 1:
            temp = pow(temp, 2, p)
            i += 1
        
        if i == m - 1 and temp != 1:
            return None
        
        b = pow(c, 2**(m - i - 1), p)
        
        m = i
        c = pow(b, 2, p)
        t = (t * c) % p
        r = (r * b) % p
    
    return r

def findPointOnCurve(a, b, p):
    
    max_attempts = 100
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        
        x = random.randint(1, p - 1)
        
        right_side = (pow(x, 3, p) + (a * x) % p + b) % p
        
        y = tonelliShanks(right_side, p)
        
        if y is not None:
            if random.choice([True, False]):
                y = (p - y) % p
            return (x, y)
    
    raise ValueError(f"Could not find a point on the curve after {max_attempts} attempts")

def generateEcdhParameters(key_size=128):
    
    print(f"Generating ECDH parameters for {key_size}-bit security:")
    startTime = time.time()

    
    lower_bound = 2**(key_size - 1)
    upper_bound = 2**key_size - 1
    
    P = sympy.randprime(lower_bound, upper_bound)

    # print("  P = ",P)
    
    while True:
        a = random.randint(0, P-1)
        b = random.randint(0, P-1)
        discriminant = (4 * pow(a, 3, P) + 27 * pow(b, 2, P)) % P
        
        if discriminant != 0:
            break

    # print("  a = ",a)
    # print("  b = ",b)

    
    G = findPointOnCurve(a, b, P)
    
    # print("  G = ",G)
    
    x, y = G
    left_side = pow(y, 2, P)
    right_side = (pow(x, 3, P) + (a * x) % P + b) % P
    assert left_side == right_side, "Point G is not on the curve!"
    # print("  Verified: Point G is on the curve y² = x³ + ax + b (mod P)")
    
    totalTime = time.time() - startTime
    # print(f"Parameter generation completed in {totalTime:.6f} seconds")
    
    return P, a, b, G



def pointAddition(P1, P2, a, p):
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    
    x1, y1 = P1
    x2, y2 = P2
    
    if x1 == x2 and y1 == (p - y2) % p:
        return None 
    
    if x1 == x2 and y1 == y2: 
        if y1 == 0:
            return None
        
        numerator = (3 * pow(x1, 2, p) + a) % p
        denominator = (2 * y1) % p
        
        invDenominator = pow(denominator, p - 2, p)
        slope = (numerator * invDenominator) % p
    else:
        numerator = (y2 - y1) % p
        denominator = (x2 - x1) % p
        
        invDenominator = pow(denominator, p - 2, p)
        slope = (numerator * invDenominator) % p
    
    x3 = (pow(slope, 2, p) - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p
    
    return (x3, y3)

def scalarMultiplication(k, point, a, p):
    
    if k == 0 or point is None:
        return None  
    
    if k < 0:
        x, y = point
        point = (x, (-y) % p)
        k = -k
        
    result = None  
    addend = point
    
    while k > 0:
        if k & 1:
            result = pointAddition(result, addend, a, p)
        addend = pointAddition(addend, addend, a, p)
        k >>= 1
    
    return result

def generatePrivateKey(key_size, p):
    return random.randint(1, p-1)

def generatePublicKey(privateKey, G, a, p):
    return scalarMultiplication(privateKey, G, a, p)

def measureKeyGenerationTime(G, a, p, key_size, num_trials=5):
    totalTime = 0
    
    for _ in range(num_trials):
        privateKey = generatePrivateKey(key_size, p)

        startTime = time.time()
        public_key = generatePublicKey(privateKey, G, a, p)
        totalTime += time.time() - startTime
    
    return totalTime / num_trials

def computeShareKey(privateKey, other_public_key, a, p):
    return scalarMultiplication(privateKey, other_public_key, a, p)

def measureSharedSecretComputationTime(privateKey, public_key, a, p, num_trials=5):
    totalTime = 0
    
    for _ in range(num_trials):
        startTime = time.time()
        shared_secret = computeShareKey(privateKey, public_key, a, p)
        totalTime += time.time() - startTime
    
    return totalTime / num_trials

def runEcdhPerformanceTest(key_size, num_trials=5):
    print(f"\nRunning ECDH performance test for {key_size}-bit key:")
    P, a, b, G = generateEcdhParameters(key_size)
    
    alicePrivateKey = generatePrivateKey(key_size, P)
    print(f"  Alice's private key: {alicePrivateKey}")
    
    startTime = time.time()
    alicePublicKey = generatePublicKey(alicePrivateKey, G, a, P)
    aliceTime = time.time() - startTime
    
    print(f"  Alice's public key: {alicePublicKey}")
    print(f"  Alice's public key generated in {aliceTime:.6f} seconds")
    
    print("\nGenerating Bob's key pair:")
    bobPrivateKey = generatePrivateKey(key_size, P)
    print(f"  Bob's private key: {bobPrivateKey}")
    
    startTime = time.time()
    bobPublicKey = generatePublicKey(bobPrivateKey, G, a, P)
    bobTime = time.time() - startTime
    
    print(f"  Bob's public key: {bobPublicKey}")
    print(f"  Bob's public key generated in {bobTime:.6f} seconds")
    
    print("\nComputing shared secrets:")
    
    startTime = time.time()
    aliceSharedKey = computeShareKey(alicePrivateKey, bobPublicKey, a, P)
    aliceSharedTime = time.time() - startTime
    
    startTime = time.time()
    bobSharedKey = computeShareKey(bobPrivateKey, alicePublicKey, a, P)
    bobSharedTime = time.time() - startTime
    
    shared_secretTime = (aliceSharedTime + bobSharedTime) / 2
    
    print(f"  Alice computes shared secret: {aliceSharedKey}")
    print(f"  Bob computes shared secret: {bobSharedKey}")
    
    assert aliceSharedKey == bobSharedKey, "Error: Shared secrets don't match!"
    
    print(f"  Shared secret (x-coordinate): {aliceSharedKey[0]}")
    print(f"  Shared secret computed in average {shared_secretTime:.6f} seconds")
    
    print(f"\nMeasuring average times over {num_trials} trials:")
    
    alice_key_avgTime = measureKeyGenerationTime(G, a, P, key_size, num_trials)
    bob_key_avgTime = measureKeyGenerationTime(G, a, P, key_size, num_trials)
    
    shared_key_avgTime = measureSharedSecretComputationTime(
        alicePrivateKey, bobPublicKey, a, P, num_trials
    )
    
    print(f"  Average time for Alice's key generation: {alice_key_avgTime:.6f} seconds")
    print(f"  Average time for Bob's key generation: {bob_key_avgTime:.6f} seconds")
    print(f"  Average time for shared secret computation: {shared_key_avgTime:.6f} seconds")
    
    return {
        "A": alice_key_avgTime,
        "B": bob_key_avgTime,
        "shared_key": shared_key_avgTime
    }


def main():
    random.seed(42)
    
    key_sizes = [128, 192, 256]
    results = {}
    
    for key_size in key_sizes:
        results[key_size] = runEcdhPerformanceTest(key_size)
    
    print("\nPerformance Results (Average of 5 trials):")
    print("=" * 60)
    print(f"{' ':8} | {'Computation Time For':^45}")
    print(f"{'k':^8} | {'':45}")
    print(f"{'':8} | {'A':^15} | {'B':^15} | {'shared key R':^15}")
    print("-" * 60)
    
    for key_size in key_sizes:
        times = results[key_size]
        print(f"{key_size:<8} | {times['A']:<15.6f} | {times['B']:<15.6f} | {times['shared_key']:<15.6f}")
    
    print("=" * 60)


if __name__ == "__main__":
    main()