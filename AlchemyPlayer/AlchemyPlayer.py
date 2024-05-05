from random import *
from PIL import Image
import glob
import os
import copy
import math
import re

G_GENERATE_VISUAL_OUTPUT = False
G_GENERATE_PRINT_VERBOSE = False
G_GENERATE_PRINT_TESTS = True
G_GENERATE_SPREADSHEET = False
G_ITERATIONS = 100
G_USE_PRESETS = False

G_REMOVE_DIAGONAL_BIAS = False

G_RECURSIVE_FITNESS = False # Do not use!
G_RECURSIVE_DEPTH = 1

G_CHANCES = 3
G_SHAPENUM = 4
G_COLORNUM = 4
G_DIMX, G_DIMY = (11,11)

G_BLOCK_CHANCE = 0.05

G_FIT_GOLDMULT = 10
G_FIT_NO_RETREAD_MULT = 1
G_FIT_PROBSOLVER = 20
G_FIT_PROBMAKER = 1 # Currently does nothing
G_FIT_LIKES_NEIGHBORS = 1
G_FIT_NUM_SIGILS = 10

G_PRESETS = [(G_FIT_GOLDMULT,G_FIT_NO_RETREAD_MULT,G_FIT_PROBSOLVER,G_FIT_PROBMAKER,G_FIT_LIKES_NEIGHBORS,G_FIT_NUM_SIGILS)]

color_map = [
    [255,255,255],
    [255,0,0],
    [0,255,0],
    [0,0,255],
    [255,127,0],
    [0,255,255]
]

def load_presets():
    for p in [-1000, -100, -10, -3, -1, 0, 1, 3, 10, 100, 1000]:
        for i in range(6):
            temp = [1,1,1,1,1,1]
            temp[i] = p
            G_PRESETS.append(tuple(temp))

class Sigil:
    def __init__(this, x, y, color, shape):
        this.x = x
        this.y = y
        this.color = color
        this.shape = shape
        pass

    def __str__(this):
        return ("[" + str(this.x) + ", " + str(this.y) + ", " + str(this.color) + ", " + str(this.shape) + "]")
    
    def match(self, other):
        return ((self.color == other.color) or self.color == 0 or other.color == 0) or ((self.shape == other.shape) or self.shape == 0 or other.shape == 0)

def num_solutions(B,x,y):
    if x <= 0 or x >= G_DIMX-1 or y <= 0 or y >= G_DIMY-1:
        return 0
    
    sum_sol = 0
    for s in range(G_SHAPENUM):
        for c in range(G_COLORNUM):
            temp = Sigil(x,y,s,c)

            # is the spot None?
            # does the spot have neighbors?
            # does the sigil match a neighbor?

            if B[y][x] == None and (B[y-1][x] != None or B[y+1][x] != None or B[y][x-1] != None or B[y][x+1] != None) and (B[y-1][x] == None or B[y-1][x].match(temp)) and (B[y+1][x] == None or B[y+1][x].match(temp)) and (B[y][x-1] == None or B[y][x-1].match(temp)) and (B[y][x+1] == None or B[y][x+1].match(temp)):
                sum_sol = sum_sol + 1
    return sum_sol

class BoardState:
    def __init__(this, m, b, bb, c):
        this.move = m
        this.board = b
        this.backboard = bb
        this.chances = c
        this.depth = 1

    def fitness(this):

        #G_FIT_GOLDMULT, G_FIT_NO_RETREAD_MULT, G_FIT_PROBSOLVER, G_FIT_PROBMAKER, G_FIT_LIKES_NEIGHBORS, G_FIT_NUM_SIGILS

        # does the move gild a tile? Y/N
        # does the move land on a gilded tile? Y/N
        # how many moves were possible on that tile?
        # how many moves does the move create?
        # how many neighbors does the tile have?
        # how many sigils are there total?


        t_bb = copy.deepcopy(this.backboard)

        sum_fit = 0

        x,y = (this.move.x,this.move.y)

        t_bb[y][x] = 1
        if board_completed(t_bb):
            return 999999999
        elif (sum(sum(t_bb,[])) > sum(sum(this.backboard,[]))):
            sum_fit = sum_fit + 300*G_FIT_GOLDMULT
        elif (sum(sum(t_bb,[])) == sum(sum(this.backboard,[]))):
            sum_fit = sum_fit - 300*G_FIT_NO_RETREAD_MULT
            pass

        for neighbor in [this.board[y+1][x], this.board[y-1][x], this.board[y][x+1], this.board[y][x-1]]:
            sum_fit = (neighbor != None and sum_fit + 66*G_FIT_LIKES_NEIGHBORS or sum_fit)

        sum_fit = sum_fit + (20 - num_solutions(board, x, y)) * G_FIT_PROBSOLVER

        temp = copy.deepcopy(board)
        temp[y][x] = this.move

        update_board(temp)

        for i in range(1,len(temp)-1):
            for j in range(1,len(temp[i])-1):
                if temp[i][j] != None:
                    sum_fit = sum_fit + G_FIT_NUM_SIGILS

        return sum_fit

backboard = [[0 for _ in range(G_DIMX)] for _ in range(G_DIMY)]
board = [[None for _ in range(G_DIMX)] for _ in range(G_DIMY)]
c = min(G_DIMX,G_DIMY)//2
board[c][c] = Sigil(c,c,0,0)
backboard[c][c] = 1

def board_completed(B):
    complete = True
    for i in range(1,len(B)-1):
        for j in range(1,len(B[i])-1):
            if B[i][j] == 0:
                complete = False
    return complete

def print_board(B):
    print("BOARD")
    for i in range(len(B)):
        b = B[i]
        temp = ""
        for j in range(len(b)):
            bb = B[i][j]
            bars = (backboard[i][j] == 1 and ["{","}"]) or ["[","]"]
            if bb == None:
                temp = temp + bars[0] + " " + bars[1] + " "
            else:
                temp = temp + bars[0] + str(bb.color) + str(bb.shape) + bars[1] + " "
        print(temp)

def update_board(B):

    for i in range(1,G_DIMY-1):
        for j in range(1,G_DIMX-1):
            if B[i][j] == None:
                break
            if j == G_DIMX-2:
                #print("filled")
                #B[i] = [None for _ in range(dim_x)]
                for k in range(1,G_DIMX-1):
                    B[i][k] = None

    for j in range(1,G_DIMX-1):
        for i in range(1,G_DIMY-1):
            if B[i][j] == None:
                break
            if i == G_DIMY-2:
                #print("filled Y")
                for k in range(1,G_DIMY-1):
                    B[k][j] = None

def filter_function(v, other):
    if v == None or (other != None and (other.shape != v[0] and other.shape != 0 and v[0] != 0 and other.color != v[1] and other.color != 0 and v[1] != 0)):
        return False
    return True

def elim_options(B,x,y):
    if B[y][x] != None or (B[y+1][x] == None and B[y-1][x] == None and B[y][x+1] == None and B[y][x-1] == None):
        return []
    
    potential_options = [(0,0)]

    for s in range(1,G_SHAPENUM):
        for c in range(1,G_COLORNUM):
            potential_options.append((s,c))

    potential_options = list(filter(lambda n: filter_function(n, B[y+1][x]),potential_options))
    potential_options = list(filter(lambda n: filter_function(n, B[y-1][x]),potential_options))
    potential_options = list(filter(lambda n: filter_function(n, B[y][x+1]),potential_options))
    potential_options = list(filter(lambda n: filter_function(n, B[y][x-1]),potential_options))

    return potential_options

def get_all_boards(BS):
    B = BS.board
    options = []
    for y in range(1,G_DIMY-1):
        for x in range(1,G_DIMX-1):
            if B[y][x] != None or (B[y+1][x] == None and B[y-1][x] == None and B[y][x+1] == None and B[y][x-1] == None):
                continue
            iter_options = elim_options(B,x,y)
            for (s,c) in iter_options:
                temp = Sigil(y,x,s,c)
                new_BS = copy.deepcopy(BS)
                new_BS.move = temp
                new_BS.depth = BS.depth + 1
                new_BS.backboard[y][x] = 1
                new_BS.board[y][x] = temp
                update_board(new_BS.board)
                options.append(new_BS)
    return options

def recursive_fitness(BS, depth):

    if depth >= G_RECURSIVE_DEPTH:
        return BS.fitness()

    sum = 0

    board_list = get_all_boards(BS)

    for ibs in board_list:
        if depth + 1 < G_RECURSIVE_DEPTH:
            sum = sum + recursive_fitness(ibs, depth + 1)

    if sum == 0 or len(board_list) == 0:
        return 0
    else:
        return sum/len(board_list)


def iterate():

    B = board

    chance_diff = 0

    options = []

    temp_color, temp_shape = (randint(1,G_COLORNUM),randint(1,G_SHAPENUM))

    if G_BLOCK_CHANCE != 0 and randint(1,math.floor(1/G_BLOCK_CHANCE)) == math.floor(1/G_BLOCK_CHANCE):
        temp_color, temp_shape = (0,0)

    temp = Sigil(-1,-1,temp_color,temp_shape)

    for y in range(1,G_DIMY-1):
        for x in range(1,G_DIMX-1):
            if B[y][x] == None and (B[y-1][x] != None or B[y+1][x] != None or B[y][x-1] != None or B[y][x+1] != None) and (B[y-1][x] == None or B[y-1][x].match(temp)) and (B[y+1][x] == None or B[y+1][x].match(temp)) and (B[y][x-1] == None or B[y][x-1].match(temp)) and (B[y][x+1] == None or B[y][x+1].match(temp)):
                #options.append(Sigil(y,x,temp_color,temp_shape))
                options.append(BoardState(Sigil(y,x,temp_color,temp_shape), board, backboard,G_CHANCES))

    #print(len(options))

    if G_RECURSIVE_FITNESS:
        options.sort(key = lambda x : recursive_fitness(x,0))
    else:
        options.sort(key = lambda x : x.fitness())

    selected = Sigil(-1,-1,-1,-1)

    if len(options) != 0:

        if G_REMOVE_DIAGONAL_BIAS:
            rev_index = 0
            rev_max = options[0].fitness()

            for i in range(0,len(options)-1,1):
                if rev_max != options[i].fitness():
                    break
                rev_index = i
            
            temp = rev_index == 0 and options[0] or options[randint(0,rev_index)]
            options = [temp] + options[rev_index:(len(options)-1)]

        chance_diff = 1
        if len(options) == 1:
            selected = options[0].move
            #print(options[0].fitness())
        else:
            #selected = options[randint(0,len(options)-1)].move
            selected = options[len(options)-1].move
            #print(options[len(options)-1].fitness())

        backboard[selected.x][selected.y] = 1
        B[selected.x][selected.y] = selected
    else:
        chance_diff = -1

    update_board(B)

    return [chance_diff,B,selected]

def canvas_create(num):

    canvas = Image.new('RGB',((G_DIMX-2)*50, (G_DIMY-2)*50), (250,250,250))
    
    for i in range(1,G_DIMY-1):
        for j in range(1,G_DIMX-1):

            if board[i][j] == None:
                img = Image.open("resources\\symbol0.gif")
            elif board[i][j].color == 0 and board[i][j].shape == 0:
                img = Image.open("resources\\nullblock.png")
                pass
            else:
                img = Image.open("resources\\symbol" + str(board[i][j].shape) + ".gif")
            
            img = img.convert("RGB")

            d = img.getdata()
            
            new_image = []
            for item in d:
            
                # change all white (also shades of whites)
                # pixels to specified color

                if board[i][j] != None:
                    spec_color = color_map[board[i][j].color]
                else:
                    spec_color = backboard[i][j] == 1 and (252,200//(4-G_CHANCES),0) or (0,0,0)
                
                if item[0] in list(range(15, 256)):

                    if G_CHANCES == 0:
                        new_image.append(backboard[i][j] == 1 and (item[0],item[1],item[2]) or (0,0,0))
                    else:
                        red = int(spec_color[0]*item[0]/255)
                        green = int(spec_color[1]*item[1]/255)
                        blue = int(spec_color[2]*item[2]/255)
                        
                        new_image.append((red,green,blue))
                else:
                    new_image.append((252,200//(4-G_CHANCES),0))
            
            # update image data
            img.putdata(new_image)

            canvas.paste(img,(50*(i-1),50*(j-1)))
            
            # save new image

    canvas.save("canvas\\canvas" + str(num) +".png")

output = open("alchemists_notes.csv", "w")

if G_USE_PRESETS:
    load_presets()

for p in G_PRESETS:

    wins, losses, avg_turns = (0,0,0)

    (G_FIT_GOLDMULT, G_FIT_NO_RETREAD_MULT, G_FIT_PROBSOLVER, G_FIT_PROBMAKER, G_FIT_LIKES_NEIGHBORS, G_FIT_NUM_SIGILS) = p

    if len(G_PRESETS) != 1: print(p)

    for i in range(G_ITERATIONS):

        inc = 0

        files = glob.glob('canvas/*')
        for f in files:
            os.remove(f)

        backboard = [[0 for _ in range(G_DIMX)] for _ in range(G_DIMY)]
        board = [[None for _ in range(G_DIMX)] for _ in range(G_DIMY)]
        c = min(G_DIMX,G_DIMY)//2
        board[c][c] = Sigil(c,c,0,0)
        backboard[c][c] = 1
        G_CHANCES = 3

        render_list = []

        if G_GENERATE_VISUAL_OUTPUT: canvas_create(0)

        while not board_completed(backboard) and G_CHANCES > 0:
            iter = iterate()
            board = iter[1]
            G_CHANCES = min(G_CHANCES + iter[0],3)
            #print_board(board)
            inc = inc + 1

            if G_GENERATE_PRINT_VERBOSE: print(str(inc) + " : " + str(iter[2]) + " : " + str(G_CHANCES))

            if G_GENERATE_VISUAL_OUTPUT: canvas_create(inc)

        if G_CHANCES > 0:
            wins = wins + 1
        else:
            losses = losses + 1

        if G_GENERATE_PRINT_TESTS: print("Test " + str(i+1) + ": " + str(inc) + " iterations")
        avg_turns = avg_turns + inc

        if G_GENERATE_VISUAL_OUTPUT:
            files = glob.glob('canvas/*.png')
            files = sorted(files, key=lambda x:float(re.findall(r"(\d+)",x)[0]))

            for filename in files: # change ending to jpg or jpeg is using those image formats
                im=Image.open(filename)
                render_list.append(im)

            render_list[0].save("canvas" + str(i) + ".gif", save_all=True, format="GIF", append_images=render_list, optimize=False, duration=100, loop=1)

    print(str(wins) + " wins, " + str(losses) + " losses, average turns: " + str(avg_turns/G_ITERATIONS) + " : win percentage: " + str(wins/(wins+losses)))

    if G_GENERATE_SPREADSHEET:
        for pp in p:
            output.write(str(pp) + ",")
        output.write(str(wins) + "," + str(losses) + "," + str(avg_turns/G_ITERATIONS) + '\n')

output.close()
