import pandas as pd

a = float("inf")
G = {1: {2:10, 3:13, 4:a, 5:a, 6:a,7:22,8:a,9:a,10:a},
     2: {1:10, 3:a, 4:9, 5:a, 6:a,7:14,8:a,9:a,10:a},
     3: {1:13, 2:a, 4:19, 5:31, 6:20,7:a,8:a,9:a,10:a},
     4: {1:a, 2:9, 3:19, 5:10, 6:a,7:11,8:4,9:7,10:a},
     5: {1:a, 2:a, 3:31, 4:10, 6:9,7:a,8:a,9:8,10:a},
     6: {1:a, 2:a, 3:20, 4:a, 5:9,7:a,8:a,9:15,10:a},
	 7:{1:22, 2:14, 3:a, 4:11, 5:a,6:a,8:a,9:a,10:8},
	 8:{1:a, 2:a, 3:a, 4:4, 5:a,6:a,7:a,9:5,10:6},
	 9:{1:a, 2:a, 3:a, 4:7, 5:8,6:15,7:a,8:5,10:4},
	 10:{1:a, 2:a, 3:a, 4:a, 5:a,6:a,7:8,8:6,9:4}
     }

name={1:"南京理工大学",2:"月牙湖",3:"钟山风景区",4:"总统府",5:"玄武湖",6:"红山动物园",7:"夫子庙",8:"新街口",9:"南京大学",10:"朝天宫"}


#去除出发点
def get_now(name,vs):
    name_now=[]
    num_now=[]
    for i in range(1,11):
        if(vs!=i):
            temp=name[i]
            name_now.append(temp)
            num_now.append(i)
    return name_now,num_now


# 对字典按键排序,返回字典
def sortk(d):
    return dict(sorted(d.items(), key=lambda k: k[0]))


def dijkstra(vs,ve,show):
    lists1 = G[vs]  # 获取起点到其他各顶点的初始路程
    show = show.append(lists1, ignore_index=True)  #初试距离
    path = [ve]
    v = min(lists1, key=lists1.get)  # 得到离起点最近的点（就是lists1的键）
    lists3 = {v: vs}      # 记录前驱节点,最后用于总结路径
    lists2 = {}           # 记录每一次迭代之后出发点到各点的距离
    ##############################
    while ve not in lists2:
        #print(lists2)
        v = min(lists1, key=lists1.get)  # 找到离起点最近的点
        lists2[v] = lists1[v]
        del lists1[v]
        for key, value in list(lists1.items()):
            if value > lists2[v] + G[v][key]:
                lists1[key] = lists2[v] + G[v][key]
                lists3[key] = v
        lists4={}     #将list1和list2合并，每次输出权重
        lists4.update(lists1)
        lists4.update(lists2)
        temp=sortk(lists4)
        show=show.append(temp,ignore_index=True)
    length = lists2[ve]
    #print(lists3)
    #print(path)
    while vs not in path:
        for k in list(lists3.keys()):
            if k == ve:
                path.append(lists3[k])
                ve = lists3[k]
                del lists3[k]
        #print(path)
    path.reverse()
    #############################
    return path,length,show


print("\n=== Dijkstra ===")
print("在下列景点间寻找起点到终点的最短路径:")
print(name)
vs = int(input("请输入起点对应的数字:"))
ve = int(input("请输入终点对应的数字:"))
if vs > 11:
    print("起点超出范围！")
if ve > 11:
    print("终点超出范围！")
else:
    name_now,num_now=get_now(name,vs)
    show = pd.DataFrame(columns=num_now)
    result = dijkstra(vs,ve,show)
    show=result[2]
    show.columns=name_now
    print()
    print(show)
    print('length = ',result[1])
    #print('The shortest path is ',result[0])
    count=len(result[0])
    for i in range(0,count-1):
         print(name[result[0][i]],end="->")
    print(name[result[0][count-1]])














