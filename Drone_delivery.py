import pygame
import numpy as np
import random
from collections import deque
import time
from itertools import permutations

# Constants
WINDOW_SIZE = 600
MAP_SIZE = 20  # 地图大小
CELL_SIZE = WINDOW_SIZE // MAP_SIZE  # 每个单元格大小
DRONE_SPEED = 1  # 无人机速度（每秒几个单元格）
TOTAL_TIME=20  #无人机最大工作时间

# Colors (RGB)
WHITE = (255, 255, 255)
GREEN=hex(0x1dda3f)
BLUE=hex(0x6373ff)
YELLOW=(255,0,0)
LIGHT_YELLOW = (255, 255, 224)
ORDER_COLOR = (255, 165, 0)  # 有订单颜色（橙色）
DRONE_COLOR = (144,215,236)  # 无人机颜色
RED=(255,0,0)

class DeliveryCenter:
    def __init__(self, pos):
        self.pos = pos
        self.delivery_points = []  # 该配送中心管理的配送点列表
        self.drones = []  # 分配给该配送中心的无人机列表

class DeliveryPoint:
    def __init__(self, pos):
        self.pos = pos
        self.delivery_center = None  # 距离最近的配送中心
        self.min_dist = -1  # 最短距离
        self.have_order = False  # 是否有订单
        self.sended=0  #是否已派送
        self.last_departure_time = -1  # 最晚出发时间
        #剩余时间
        self.remain_time=-1
        self.expected_delivery_time =None #预计送达时间
        self.latest_arrival_time = None  # 最晚到达时间
        self.drone_id=None  # 正在运送的无人机id

# 从文件加载地图数据
def load_map_from_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    # 读取地图大小
    map_size = tuple(map(int, lines[0].strip().split()))
    num_rows, num_cols = map_size
    map_data = np.zeros((num_rows, num_cols), dtype=int)

    # 读取地图数据
    for i in range(1, num_rows + 1):
        row_data = list(map(int, lines[i].strip().split()))
        for j in range(num_cols):
            map_data[i - 1, j] = row_data[j]

    return map_data

# 查找最近的配送中心
def find_nearest_center(map_data, point):
    centers = np.argwhere(map_data == 1)
    min_dist = float('inf')
    nearest_center = None
    for center in centers:
        dist = np.linalg.norm(np.array(center) - np.array(point))
        if dist < min_dist:
            min_dist = dist
            nearest_center = tuple(center)
    return nearest_center, min_dist

# 初始化pygame
pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
caption='无人机配送系统'
pygame.display.set_caption(caption)

# 从文件加载地图
map_filename = 'map.txt'
map_data = load_map_from_file(map_filename)

# 创建配送中心和配送点
delivery_centers = {}
delivery_points = []
for row in range(MAP_SIZE):
    for col in range(MAP_SIZE):
        if map_data[row, col] == 1:
            delivery_centers[(row, col)] = DeliveryCenter((row, col))
        elif map_data[row, col] >= 2:
            delivery_point = DeliveryPoint((row, col))
            delivery_points.append(delivery_point)

# 将每个配送点分配给最近的配送中心
for point in delivery_points:
    nearest_center, min_dist = find_nearest_center(map_data, point.pos)
    point.delivery_center = nearest_center
    point.min_dist = min_dist
    delivery_centers[nearest_center].delivery_points.append(point)

# 生成随机订单
def generate_orders(current_time):
    #print("\n生成订单")
    for point in delivery_points:
        if point.sended==1:
            #print(f"配送点{point.pos}正在派送")
            continue
        if random.random() < 0.1:  # 10% 的概率生成订单
            initial_time = random.choice([30,30,30, 45,45, 60])  # 初始时间
            #print(f"在 {point.pos} 生成订单，最晚出发时间 {point.last_departure_time}")
            latest_departure_time = current_time + initial_time - (point.min_dist / DRONE_SPEED)
            point.have_order = True
            if point.last_departure_time == -1 or latest_departure_time < point.last_departure_time:
                point.last_departure_time = latest_departure_time
            #print(f"在 {point.pos} 生成订单，最晚出发时间 {point.last_departure_time},当前最晚出发时间{latest_departure_time},当前时间{current_time},初始时间{initial_time}，最短距离{point.min_dist}")
                point.remain_time=initial_time
            point.latest_arrival_time=current_time+initial_time
            map_data[point.pos[0], point.pos[1]] = 3  # 更改配送点颜色表示有订单


drone_id=11
drone_id_now=1

# 分配订单给无人机
def assign_orders(current_time):
    print("\n\n分配订单给无人机")
    for center in delivery_centers.values():
        orders = [point for point in center.delivery_points if point.have_order]
        if not orders:
            #print(f"配送中心 {center.pos} 没有订单")
            continue

        # 按最晚出发时间排序订单
        sorted_orders = sorted(orders, key=lambda x: x.last_departure_time)

        # 检查最早要出发的订单
        earliest_departure_time = sorted_orders[0].last_departure_time
        #print("最早要出发的订单:"f"{earliest_departure_time}")
        # 为单个无人机分配要交付的订单
        
        if sorted_orders and earliest_departure_time <= current_time+10:
            print(f"配送中心 {center.pos} 的订单:", [(point.pos, point.last_departure_time) for point in sorted_orders])
            print("最早要出发的订单:"f"{earliest_departure_time}")
            global drone_id
            if(drone_id==37):
                drone_id=11
            drone = {'pos': center.pos, 'targets': [], 'path': [], 'current_target': None,'last_pos':center.pos,'last_pos_value':1,'id':drone_id,"in_free_point":False,"in_busy_point":False,'total_time':0}
            
            current_time_needed = 0
            print("当前无人机：",chr(drone_id+54))
            drone_id += 1

            #######处理targets、path######
            #添加最紧急
            drone['targets'].append(sorted_orders[0])
            drone['path']=drone['targets'][0]
            drone['total_time']+=sorted_orders[0].min_dist/DRONE_SPEED

            sorted_orders[0].have_order = False
            sorted_orders[0].sended=1
            sorted_orders[0].drone_id=drone['id']
            sorted_orders[0].expected_delivery_time=current_time+sorted_orders[0].min_dist/DRONE_SPEED
            init_delivery_time=sorted_orders[0].expected_delivery_time
            print("第一单预计送达时间："f"{sorted_orders[0].expected_delivery_time}")
            
            ##删除sorted_orders的第一个元素
            sorted_orders.remove(sorted_orders[0])

            for order in sorted_orders:
                print("\n开始处理order:",order.pos)
                drone['targets'].append(order)

                #当场检验
                # 计算无人机的最佳路径
                if drone['targets'].__len__() > 1:
                    #_,drone['path'] = weighted_tsp(center.pos, drone['targets'],current_time)
                    print("无人机的目标点：",[(a.pos) for a in drone['targets']])
                    temp_path,flag = calculate_optimal_path(drone['targets'][0], drone['targets'][1:],init_delivery_time,current_time)
                    if(flag==False):
                        print("路径计算失败，重新计算路径")
                        #将order从drone['targets']中删除
                        drone['targets'].remove(order)
                    else:                     
                        #成功
                        print("路径成功")
                        drone['path'] = temp_path
                        order.have_order = False
                        order.sended=1
                        order.drone_id=drone['id']
                        #将order从sorted_orders中删除
                        sorted_orders.remove(order)
                        #center.delivery_points.remove(order)
        
            #####得到最终路径后，准备出发--处理path
            ##注意，drone,target为delivery_point类型,path,current_target,后文的target都为pos类型
            drone['path']=list(a.pos for a in drone['targets'])
            drone['current_target'] = drone['path'][0]
            center.drones.append(drone)
            print(f"从 {center.pos} 派出无人机，路径: {drone['path']},下一个目标点：{drone['current_target']}")

            


# 计算最佳路径（旅行商问题）
def calculate_optimal_path(start, targets, init_delivery_time,current_time):
    print("起点与中间点", start.pos, [(t.pos, t.last_departure_time) for t in targets])
    min_path = None
    min_distance = float('inf')
    all_points = [start.pos] + [t.pos for t in targets]
    total_time=init_delivery_time-current_time
    
    for perm in permutations(targets):
        perm_with_start = [start.pos] + [t.pos for t in perm]  # 包含起点的路径
        distance = sum(calculate_distance(perm_with_start[i], perm_with_start[i + 1]) for i in range(len(perm_with_start) - 1))
        if distance >= min_distance:  #检验路径长度
            print("当前最小值:",distance)
            continue

        expected_times = []
        current_point=start
        current_pos = start.pos
        current_delivery_time = init_delivery_time
        flag = True
        for point in perm:
            print("COP 开始处理",point.pos,"初始运动时间为：",total_time)
            # 检查是否有任何一个点的预计送达时间超过了其最晚到达时间
            travel_time = calculate_distance(current_pos, point.pos)+point.min_dist/DRONE_SPEED   #包含从该点回到配送中心的时间
            if(travel_time-2*point.min_dist/DRONE_SPEED>current_point.min_dist/DRONE_SPEED):
                print("路径计算失败，距离太长! 去这个点的路径长为：",travel_time,"不去这个点的路径为：",point.min_dist/DRONE_SPEED*2+current_point.min_dist/DRONE_SPEED)
                flag=False
                break
            current_delivery_time += travel_time
            point.expected_delivery_time = current_delivery_time
            expected_times.append((point.pos, current_delivery_time))
            current_pos = point.pos
            current_point=point
            # 检查是否有任何一个点的预计送达时间超过了其最晚到达时间
            if point.latest_arrival_time is not None and current_delivery_time > point.latest_arrival_time:
                print("该配送点会超时",point.pos,point.latest_arrival_time,current_delivery_time)
                flag = False
                break
            
            total_time += travel_time
            # 检查无人机是否超时
            if(total_time>TOTAL_TIME):
                print("无人机没电了",total_time,travel_time)
                flag = False
                break
        
        if flag==True:
            min_distance = distance
            min_path = perm

    print("最短路径:", [(start.pos, current_time+start.expected_delivery_time)] + expected_times)
    if(min_path):
        print("minpath:",(a.pos for a in min_path))
    else:
        print("事实上没有可用的路径了")
    return min_path, flag

# 计算两点之间的距离
def calculate_distance(point1, point2):
    return np.linalg.norm(np.array(point1) - np.array(point2))

# 移动无人机
def move_drones(current_time):
    #print("/n移动无人机")
    for center in delivery_centers.values():
        for drone in center.drones:
            if drone['current_target']:  #如果还有下一个目标
                #print("无人机当前位置:", drone['pos'],"目标位置:", drone['current_target'])
                current_pos = drone['pos']
                target = drone['current_target']
                
                
                #恢复上一个空格的颜色
                #print(drone['last_pos_value'])

                if(drone['last_pos_value']==0):
                    #print(f"恢复上一个空格{drone['last_pos']}的颜色")
                    map_data[drone['last_pos']]= drone['last_pos_value']  # 用于表示无人机路径的临时值
                elif(drone['last_pos_value']==2):
                    #print(f"恢复上一个空格{drone['last_pos']}的颜色")
                    map_data[drone['last_pos']]= drone['last_pos_value']  # 用于表示无人机路径的临时值
                elif(drone['last_pos_value']==3):
                    #print(f"恢复上一个空格{drone['last_pos']}的颜色")
                    map_data[drone['last_pos']]= drone['last_pos_value']  # 用于表示无人机路径的临时值

                
                
                drone['last_pos_value'] = map_data[current_pos]  #记录当前单元格的值
                drone['last_pos'] = current_pos  #记录当前单元格的位置

                #绘制当前颜色
                if(map_data[current_pos]==0):
                    map_data[current_pos] = drone['id']  #11-36  # 用于表示无人机路径的临时值
                if(map_data[current_pos]==2):
                    map_data[current_pos] = drone['id']+100  # 用于表示无人机路径的临时值
                if(map_data[current_pos]==3):
                    map_data[current_pos] = drone['id']+200  # 用于表示无人机路径的临时值

                if current_pos != target:
                    #检查有没有中奖
                    for point in delivery_points:
                        if point.pos == current_pos and point.drone_id==drone['id']:  #由我运送
                            point.have_order = False  # 标记订单为已完成
                            point.sended=0  # 标记订单为未派送
                            point.drone_id=None  # 标记无人机为空闲
                            point.last_departure_time=-1  # 标记送点的最晚出发时间
                            point.expected_delivery_time=None  # 标记送点的预计送达时间
                            point.latest_arrival_time=None  # 标记送点的最晚到达时间
                            #map_data[current_pos] = 2  # 将配送点恢复为原始状态
                            #还不能直接回复成2，要恢复成111-137，以便本轮显示
                            map_data[current_pos] = 300+drone['id']  # 用于表示无人机路径的临时值
                            drone["last_pos_value"]=2 #该配送点重新空闲
                            #print("无人机已到达目标点:", current_pos)

                            #将该point从drone['path]中删除

                            for i,_ in enumerate(drone['path']):
                                if(drone['path'][i]==point.pos):
                                    drone['path'].pop(i)

                    #计算下一步
                    #正常行进
                    direction = np.sign(np.array(target) - np.array(current_pos))
                    new_pos = tuple(np.array(current_pos) + direction)
                    drone['pos'] = new_pos

                    #探测周边

                    #print("下一步去往:", new_pos)                       
                else:
                    for point in delivery_points:
                        if point.pos == current_pos and point.drone_id==drone['id']:  #由我运送
                            point.have_order = False  # 标记订单为已完成
                            point.sended=0  # 标记订单为未派送
                            point.drone_id=None  # 标记无人机为空闲
                            point.last_departure_time=-1  # 标记送点的最晚出发时间
                            point.expected_delivery_time=None  # 标记送点的预计送达时间
                            point.latest_arrival_time=None  # 标记送点的最晚到达时间
                            #map_data[current_pos] = 2  # 将配送点恢复为原始状态
                            #还不能直接回复成2，要恢复成111-137，以便本轮显示
                            map_data[current_pos] = 300+drone['id']  # 用于表示无人机路径的临时值
                            drone["last_pos_value"]=2 #该配送点重新空闲
                            #print("无人机已到达目标点:", current_pos)
                    if drone['path']:
                        drone['path'].pop(0)

                        if drone['path'].__len__() > 0:
                            print("无人机继续前往下一个目标点:", drone['path'][0])
                            drone['current_target'] = drone['path'][0]

                            #计算下一步
                            target = drone['current_target']
                            direction = np.sign(np.array(target) - np.array(current_pos))
                            new_pos = tuple(np.array(current_pos) + direction)
                            drone['pos'] = new_pos
                            #print("下一步去往:", new_pos)
                        else:
                            drone['current_target'] = None
                            #删除这个drone
                            center.drones.remove(drone)
                            print("无人机已回家")

# 主循环
clock = pygame.time.Clock()
running = True
current_time = 0
paused=0
FONT_SIZE=18
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        #暂停
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
                if paused:
                    print("游戏暂停")
                    time.sleep(5)
                else:
                    print("游戏继续")

    # 清空屏幕
    screen.fill(WHITE)
    print("\n当前时间:"f"{current_time}")

    # 绘制地图
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            cell_value = map_data[row, col]
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if cell_value == 0:
                pygame.draw.rect(screen, GREEN, rect)  # 空地
            elif cell_value == 1:
                pygame.draw.rect(screen, BLUE, rect)  # 配送中心
            elif cell_value == 2: 
                pygame.draw.rect(screen, LIGHT_YELLOW, rect)  # 配送点
            elif cell_value == 3:
                pygame.draw.rect(screen, ORDER_COLOR, rect)  # 带有订单的配送点
                #绘制数字
                font = pygame.font.Font(None, FONT_SIZE)
                #找到delivery_points中的对应位置的订单
                for point in delivery_points:
                    if point.pos==(row,col):
                        remain_time=point.remain_time
                        point.remain_time-=1
                        if(point.drone_id==None):
                            text=str(remain_time)
                        else:
                            text=str(remain_time)+"-"+str(chr(54+point.drone_id))
                        if(remain_time>5):
                            text = font.render(text, True, LIGHT_YELLOW)
                        else:
                            text = font.render(text, True, RED)
                        text_rect = text.get_rect(center=rect.center)
                        screen.blit(text, text_rect)

                        break
            elif (cell_value >= 11 and cell_value <= 36):
                pygame.draw.rect(screen, DRONE_COLOR, rect)  # 无人机路径
                #绘制数字
                font = pygame.font.Font(None, FONT_SIZE)

                text = font.render(str(chr(cell_value+54)), True, YELLOW)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
            elif (cell_value >= 111 and cell_value <= 136):  #空闲配送点
                pygame.draw.rect(screen, LIGHT_YELLOW, rect)  # 无人机路径
                #绘制数字
                font = pygame.font.Font(None, FONT_SIZE)

                text = font.render(str(chr(cell_value+54-100)), True, YELLOW)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
            elif (cell_value >= 211 and cell_value <= 236):  #有订单配送点
                pygame.draw.rect(screen, ORDER_COLOR, rect)  # 无人机路径
                #绘制数字
                font = pygame.font.Font(None, FONT_SIZE)

                text = font.render(str(chr(cell_value+54-200)), True, YELLOW)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
            elif (cell_value >= 311 and cell_value <= 336):  #有订单配送点
                pygame.draw.rect(screen, ORDER_COLOR, rect)  # 无人机路径
                #绘制数字
                font = pygame.font.Font(None, FONT_SIZE)

                text = font.render(str(chr(cell_value+54-300)), True, YELLOW)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)

                map_data[row, col]=2  #当场恢复
            
            

    # 生成订单
    generate_orders(current_time)

    # 分配订单给无人机
    assign_orders(current_time)

    # 移动无人机
    move_drones(current_time)

    # 更新时间
    current_time += 1

    pygame.display.set_caption(caption+f'   当前时间：{str(current_time)}') 
    # 刷新屏幕
    pygame.display.flip()

    # 控制帧率
    clock.tick(1)  # 设置帧率为10帧/秒


# 退出pygame
pygame.quit()
