import math
import time

# ============================================================
# CONFIGURATION (EDIT FREELY)
# ============================================================

initiatives = [
    ("Agriculture", 100),
    ("Industry",    99),
    ("Education",   70),
    ("Health",      60),
]

M = 5000          # Total resources
BASE = 5000       # 5000 in f(x) = 5000*x/(5000+x)
STEP = 10         # brute-force granularity

# ============================================================
# VALUE FUNCTIONS
# ============================================================

def f(x):
    if x <= 0:
        return 0
    return BASE * x / (BASE + x)

def val(x, w):
    return w * f(x)

# ============================================================
# OPTIMAL ANALYTIC SOLVER (KKT solution)
# ============================================================

def optimal_alloc(initiatives, M):
    # names = [n for (n,w) in initiatives]
    # weights = [w for (n,w) in initiatives]
    # n = len(weights)

    # sqrt_w = [math.sqrt(w) for w in weights]
    # order = sorted(range(n), key=lambda i: sqrt_w[i], reverse=True)
    # sorted_sqrt_w = [sqrt_w[i] for i in order]

    # def compute_S(k):
    #     return (M + BASE * k) / sum(sorted_sqrt_w[:k])

    # K = None
    # for k in range(1, n + 1):
    #     S_k = compute_S(k)
    #     if S_k * sorted_sqrt_w[k-1] <= BASE:
    #         K = k - 1
    #         break
    # if K is None:
    #     K = n

    # S = compute_S(K)

    # x_sorted = []
    # for j in range(K):
    #     x_sorted.append(S * sorted_sqrt_w[j] - BASE)
    # x_sorted += [0] * (n - K)

    # x = [0] * n
    # for idx, valx in zip(order, x_sorted):
    #     x[idx] = valx

    # values = [val(x[i], weights[i]) for i in range(n)]
    # return names, x, values, sum(values)

    names = [n for (n,w) in initiatives]
    weights = [w for (n,w) in initiatives]

    V = sum(math.sqrt(w) for w in weights)
    x = [ math.sqrt(w) * (M + BASE * len(initiatives)) / V - BASE for w in weights ]
    values = [val(x[i], weights[i]) for i in range(len(initiatives))]
    return names, x, values, sum(values)




# ============================================================
# HORRIBLE BRUTE-FORCE CHECKER
# ============================================================

def brute_force(initiatives, M, STEP):
    names = [n for (n,w) in initiatives]
    weights = [w for (n,w) in initiatives]
    n = len(weights)

    best_value = -1
    best_alloc = None

    def search(i, remaining, cur):
        nonlocal best_value, best_alloc

        if i == n - 1:
            alloc = cur + [remaining]
            total = sum(val(alloc[j], weights[j]) for j in range(n))
            if total > best_value:
                best_value = total
                best_alloc = alloc
            return

        for x in range(0, remaining + 1, STEP):
            search(i + 1, remaining - x, cur + [x])

    search(0, M, [])
    return names, best_alloc, [val(best_alloc[i], weights[i]) for i in range(n)], best_value

# ============================================================
# RUN BOTH WITH TIMING
# ============================================================

t0 = time.perf_counter()
names_opt, x_opt, vals_opt, total_opt = optimal_alloc(initiatives, M)
t1 = time.perf_counter()

names_bf, x_bf, vals_bf, total_bf = brute_force(initiatives, M, STEP)
t2 = time.perf_counter()

# ============================================================
# OUTPUT — OPTIMAL
# ============================================================

print("="*70)
print(" OPTIMAL ANALYTIC SOLUTION")
print("="*70)
print(f"Time: {t1 - t0:.6f} seconds\n")
print(f"{'Initiative':<15} {'Alloc':>10} {'Value':>12}")
print("-"*70)
for i in range(len(names_opt)):
    print(f"{names_opt[i]:<15} {x_opt[i]:>10.2f} {vals_opt[i]:>12.2f}")
print("-"*70)
print(f"{'TOTAL':<15} {'':>10} {total_opt:>12.2f}")

# ============================================================
# OUTPUT — BRUTE FORCE
# ============================================================

print("\n\n" + "="*70)
print(f" BRUTE FORCE CHECK (STEP={STEP})")
print("="*70)
print(f"Time: {t2 - t1:.6f} seconds\n")
print(f"{'Initiative':<15} {'Alloc':>10} {'Value':>12}")
print("-"*70)
for i in range(len(names_bf)):
    print(f"{names_bf[i]:<15} {x_bf[i]:>10.2f} {vals_bf[i]:>12.2f}")
print("-"*70)
print(f"{'TOTAL':<15} {'':>10} {total_bf:>12.2f}")

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "="*70)
print(" PERFORMANCE SUMMARY")
print("="*70)
print(f"Optimal solver time:     {t1 - t0:.6f} seconds")
print(f"Brute force time:        {t2 - t1:.6f} seconds")
print(f"Total execution time:    {t2 - t0:.6f} seconds")
print("\nDifference (opt - brute):", total_opt - total_bf)
