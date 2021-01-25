def ct(l=None):
    if l == None:
        return None
    else:
        return sum(1+ct(i) for i in l if isinstance(i,list))

def evaluate_expression(nx=None, expression=None):
    if nx == None or expression == None:
        return None
    else:
        ct1 = ct(expression)
        lst1 = []
        lst2 = []
        for i in range(1, ct1+1):
            c1 = expression[0]
            for i in range(ct1-i):
                c1 = c1[0]
            lst1.append(c1[len(c1)-1])
        lst1.append(expression[len(expression)-1])
        addr = lst1[0]
        for i in range(len(lst1)-1):
            addr = nx.peek64(addr)+lst1[i+1]
        return addr
