def f(*args):
    if len(args) != 1:
        return None
    else:
        return sum(1+f(i) for i in args[0] if isinstance(i, list))

def handle_evaluate_expression(*args):
    if len(args) != 2:
        return None
    else:
        ct1 = f(args[1])
        lst1 = []
        lst2 = []
        for i in range(1, ct1+1):
            c1 = args[1][0]
            for i in range(ct1-i):
                c1 = c1[0]
            lst1.append(c1[len(c1)-1])
        lst1.append(args[1][len(args[1])-1])
        addr = lst1[0]
        for i in range(len(lst1)-1):
            addr = args[0].peek64(addr)+lst1[i+1]
        return addr
