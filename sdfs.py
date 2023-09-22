isBInTheRoute = ((B & ((a & c & ~e) | (a & ~c & e) | (~a & c & e))) | (~B & ~a & ~c & ~e))
IsCInTheRoute = ((C & ((d & b & ~e) | (b & ~d & e) | (~b & d & e))) | (~C & ~b & ~d & ~e))  
flow_a_to_d = ((a & ~b) | (~a &b)) &  ((~c & d) | (c & ~d)) 


isAInTheRoute = (A & a & b) | (~A & ~a & ~b)
isDInTheRoute = (D & c & d) | (~D & ~c & ~d)

flow_b_to_c = ((a & ~c & ~e) | (~a & c & ~e) | (~a & ~c & e)) & \
            ((b & ~d & ~e) | (~b & d & ~e) | (~b & ~d & e))