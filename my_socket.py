import websocket
import _thread
import time
import ssl
import random
import re
import datetime

old_bullets = []
current_action = time.time()
tick_number = 0
attack_tick_number = 0

def on_message(ws, message):
    global current_action
    global tick_number
    global attack_tick_number
    tick_number+=1
    board = re.findall(r'^board=(.*)$', message)[0]
    size = round(len(board)**0.5)
    init_map = {}
    pp_map = {}
    bullet_map = {}
    antitank_map = {}
    gun_map = {}
    enemy_tanks = ('˄','˂','>','˅')
    bot_tanks = ('?','»','¿','«')
    other_tanks = ('˄','˂','>','˅','?','»','¿','«')
    my_tank = ('▲','►','▼','◄')
    constractions = {'╬':6,'╩':3,'╦':3,'╠':3,'╣':3,'╨':1, '╥':1,'╞':1,'╡':1,'│':1, '─':1, '┌':1, '┐':1,'└':1, '┘': 1,'☼':1000}
    act_objects = ('˄','˂','>','˅','?','»','¿','«','╬','╩','╦','╠','╣','╨', '╥','╞','╡','│', '─', '┌', '┐','└', '┘','•')
    add_act_objects = ('˄','˂','>','˅','?','»','¿','«','•')
    empty_objects = (' ','Ѡ','•')
    filled_objects = (' ','Ѡ','▲','►','▼','◄')
    for i in range(size):
        init_map[i] = list(board[i*size:(i+1)*size][:])
        pp_map[i] = list(board[i*size:(i+1)*size][:])
        bullet_map[i] = list(board[i*size:(i+1)*size][:])
        antitank_map[i] = list(board[i*size:(i+1)*size][:])
        gun_map[i] = list(board[i*size:(i+1)*size][:])
        print(''.join(init_map[i]))
    print(datetime.datetime.now().time(), str(time.time() - current_action))
    current_action = time.time()
    filled = True
    last_cell = size
    mytank_i, mytank_j = 1, 1
    fee = 7
    escape = 6
    gun = 6
    bullets = []
    antitanks = []
    can_attack = False
    if tick_number - attack_tick_number > 3:
        can_attack = True
    for i in range(size):
        for j in range(size):
            if pp_map[i][j] in enemy_tanks:
                pp_map[i][j] = size
                if pp_map[i][j] == '>' and pp_map[i][j + 1] in filled_objects:
                    gun_map[i][j + 1] = gun
                    if pp_map[i][j + 2] in filled_objects:
                        gun_map[i][j + 2] = gun//2
                elif pp_map[i][j] == '˂' and pp_map[i][j - 1] in filled_objects:
                    gun_map[i][j - 1] = gun
                    if pp_map[i][j - 2] in filled_objects:
                        gun_map[i][j - 2] = gun//2
                elif pp_map[i][j] == '˄' and pp_map[i - 1][j] in filled_objects:
                    gun_map[i - 1][j] = gun
                    if pp_map[i - 2][j] in filled_objects:
                        gun_map[i - 2][j] = gun//2
                elif pp_map[i][j] == '˅' and pp_map[i + 1][j] in filled_objects:
                    gun_map[i + 1][j] = gun
                    if pp_map[i + 2][j] in filled_objects:
                        gun_map[i + 2][j] = gun//2

                antitanks.append([i,j])
            elif pp_map[i][j] in bot_tanks:
                pp_map[i][j] = size//2
            elif pp_map[i][j] in my_tank:
                mytank_i, mytank_j = i, j
            if bullet_map[i][j] == '•':
                bullet_map[i][j] = fee
                bullets.append([i,j])
    
    def minus_pp(objects, object_map, fee):
        for object_i, object_j  in objects:
            for k in range(1, min(object_j + 1, fee)):
                    if object_map[object_i][object_j - k] in filled_objects:
                        object_map[bullet_i][object_j - k] = fee - k
                    else:
                        break
            for k in range(1,min(size - bullet_j,fee)):
                    if object_map[object_i][object_j + k] in filled_objects:
                        object_map[object_i][object_j + k] = fee - k
                    else:
                        break
            for k in range(1, min(object_i + 1, fee)):
                    if object_map[object_i - k][object_j] in filled_objects:
                        object_map[object_i - k][object_j] = fee - k
                    else:
                        break
            for k in range(1,min(size - object_i,fee)):
                    if object_map[object_i + k][object_j] in filled_objects:
                        object_map[object_i + k][object_j] = fee - k
                    else:
                        break
    minus_pp(bullets, bullet_map, fee)
    minus_pp(antitanks, antitank_map, fee)

    #Nearest way to tanks
    while filled:
        last_cell-=1
        filled = False
        for i in range(size):
            for j in range(size):
                if pp_map[i][j] == last_cell + 1:
                    if type(pp_map[i+1][j]) == str:
                        pp_map[i+1][j] = last_cell - constractions.get(pp_map[i+1][j],0)
                        filled = True
                    if type(pp_map[i-1][j]) == str:
                        pp_map[i-1][j] = last_cell - constractions.get(pp_map[i-1][j],0)
                        filled = True
                    if type(pp_map[i][j+1]) == str:
                        pp_map[i][j+1] = last_cell - constractions.get(pp_map[i][j+1],0)
                        filled = True
                    if type(pp_map[i][j-1]) == str:
                        pp_map[i][j-1] = last_cell - constractions.get(pp_map[i][j-1],0)
                        filled = True
    
    for i in range(size):
            for j in range(size):
                if type(pp_map[i][j]) == int:
                    if type(bullet_map[i][j]) == int:
                        pp_map[i][j] -= bullet_map[i][j]
                    if not can_attack:
                        if type(antitank_map[i][j]) == int:
                            pp_map[i][j] -= antitank_map[i][j]
                    if type(gun_map[i][j]) == int:
                        pp_map[i][j] -= gun_map[i][j]
    #Movement
    direction = random.choice(['RIGHT','LEFT','UP','DOWN'])
    try:
        max_cell = pp_map[mytank_i][mytank_j]
        if pp_map[mytank_i][mytank_j + 1] > max_cell:
            direction = 'RIGHT'
            max_cell = pp_map[mytank_i][mytank_j + 1]
        if pp_map[mytank_i][mytank_j - 1] > max_cell:
            direction = 'LEFT'
            max_cell = pp_map[mytank_i][mytank_j - 1]
        if pp_map[mytank_i - 1][mytank_j] > max_cell:
            direction = 'UP'
            max_cell = pp_map[mytank_i - 1][mytank_j]
        if pp_map[mytank_i + 1][mytank_j] > max_cell:
            direction = 'DOWN'
            max_cell = pp_map[mytank_i + 1][mytank_j]
    except:
        print(direction)
    is_act = ""
    
    #Will we attak?
    if can_attack:
        if direction == 'RIGHT':
            if (init_map[mytank_i][mytank_j + 1] in act_objects):
                is_act = ",ACT"
            elif (init_map[mytank_i][mytank_j + 1] in empty_objects):
                for i in range(1,size - mytank_j):
                    if init_map[mytank_i][mytank_j + i] not in empty_objects:
                        if init_map[mytank_i][mytank_j + i] in other_tanks:
                            is_act = ",ACT"
                        else:
                            break

        elif direction == 'LEFT':
            if (init_map[mytank_i][mytank_j - 1] in act_objects):
                is_act = ",ACT"
            elif (init_map[mytank_i][mytank_j - 1] in empty_objects):
                for i in range(1, mytank_j + 1):
                    if init_map[mytank_i][mytank_j - i] not in empty_objects:
                        if init_map[mytank_i][mytank_j - i] in other_tanks:
                            is_act = ",ACT"
                        else:
                            break

        elif direction == 'DOWN':
            if (init_map[mytank_i + 1][mytank_j] in act_objects):
                is_act = ",ACT"
            elif (init_map[mytank_i + 1][mytank_j] in empty_objects):
                for i in range(1,size - mytank_i):
                    if init_map[mytank_i + i][mytank_j] not in empty_objects:
                        if init_map[mytank_i + i][mytank_j] in other_tanks:
                            is_act = ",ACT"
                        else:
                            break

        elif direction == 'UP':
            if (init_map[mytank_i - 1][mytank_j] in act_objects):
                is_act = ",ACT"
            elif (init_map[mytank_i - 1][mytank_j] in empty_objects):
                for i in range(1, mytank_i + 1):
                    if init_map[mytank_i - i][mytank_j] not in empty_objects:
                        if init_map[mytank_i - i][mytank_j] in other_tanks:
                            is_act = ",ACT"
                        else:
                            break
    if is_act:
        attack_tick_number = tick_number
    print(direction+is_act)
    ws.send(direction+is_act)
def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        while True:
            time.sleep(10)
        ws.close()
        print("thread terminating...")
    _thread.start_new_thread(run, ())


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://dojorena.io:80/codenjoy-contest/ws?user=<userid>&code=<usercode>",
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    ws.on_open = on_open

    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False})
