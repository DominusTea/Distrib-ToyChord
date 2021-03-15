def merge_dict(x, y):
    '''
    This function merges two dictionaries
    https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-taking-union-of-dictionaries
    '''
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def get_n_consequent(overlay_dict, id_ip_dict, n, start_id):
    '''
    This function returns n consequent nodes' ips starting
    from start_id. If n > len(overlay_dict)-1, then the function Returns
    only the unique nodes.
    '''
    res_dict = {}
    temp = start_id
    for i in range(n):
        temp = overlay_dict[temp]
        if temp != start_id:
            res_dict[temp] = id_ip_dict[int(temp)]
        else:
            break
    return res_dict

if __name__ =='__main__':
    overlay_dict = {0:1, 1:2,2:3, 3:4, 4:0}
    id_ip_dict = {0:"0id", 1:"1id", 2:"2id", 3:"3id", 4:"4id"}
    n=2
    start_id = 2
    print(get_n_consequent(overlay_dict, id_ip_dict, n, start_id))
