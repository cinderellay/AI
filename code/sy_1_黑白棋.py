from tkinter import *
import time
import tkinter.messagebox
import random
import math

BOARD_SIZE = 8
PLAYER_NUM = 2
COMPUTER_NUM = 1
MAX_THINK_TIME = 60
direction = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]


def Init_Board():
    """初始化棋盘数组"""
    board = {}
    for i in range(BOARD_SIZE):
        board[i] = {}
        for j in range(BOARD_SIZE):
            board[i][j] = 0
    """初始化最中间四个黑白棋"""
    board[int(BOARD_SIZE / 2 - 1)][BOARD_SIZE / 2 - 1] = COMPUTER_NUM
    board[int(BOARD_SIZE / 2)][BOARD_SIZE / 2] = COMPUTER_NUM
    board[int(BOARD_SIZE / 2 - 1)][BOARD_SIZE / 2] = PLAYER_NUM
    board[int(BOARD_SIZE / 2)][BOARD_SIZE / 2 - 1] = PLAYER_NUM
    return board


def countTile(board, tile):  # tile表示此时棋手或电脑中的一个
    """计算总棋子数"""
    chessman = 0
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == tile:
                chessman += 1
    return chessman


def possible_positions(board, tile):
    """返回一个颜色棋子可能的下棋位置"""
    positions = []
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] != 0:
                continue
            """当该位置无棋子时，判断该位置下棋是否合法"""
            if updateBoard(board, tile, i, j, check_only=True) > 0:
                positions.append((i, j))
    return positions


def isOnBoard(x, y):
    """保证棋子在棋盘上"""
    return 0 <= x <= 7 and 0 <= y <= 7


def updateBoard(board, tile, i, j, check_only=False):
    reversed_chessman = 0
    board[i][j] = tile
    if tile == 2:
        change = 1
    else:
        change = 2
    need_turn = []
    for x_direction, y_direction in direction:
        x, y = i, j
        x += x_direction
        y += y_direction
        if isOnBoard(x, y) and board[x][y] == change:
            x += x_direction
            y += y_direction
            if not isOnBoard(x, y):
                continue
            while board[x][y] == change:
                x += x_direction
                y += y_direction
                if not isOnBoard(x, y):
                    break
            if not isOnBoard(x, y):
                continue
            if board[x][y] == tile:
                while True:
                    x -= x_direction
                    y -= y_direction
                    if x == i and y == j:
                        break
                    need_turn.append([x, y])
    board[i][j] = 0
    for x, y in need_turn:
        if not check_only:
            board[i][j] = tile
            board[x][y] = tile
        reversed_chessman += 1
    return reversed_chessman


def mctsNextPosition(board):
    """蒙特卡洛树搜索"""
    def ucb1(node_tuple, t, cval):  # 计算UCB值
        name, nplayout, reward, childrens = node_tuple

        if nplayout == 0:
            nplayout = 0.00000000001

        if t == 0:
            t = 1
        # reward 是赢的次数 nplayout是模拟对局次数,cval是常数（本程序中设为0.1）,t为当前的次数
        return (reward / nplayout) + cval * math.sqrt(2 * math.log(t) / nplayout)  # 计算UCB

    def find_playout(tep_board, tile, depth=0):
        def eval_board(tep_board):
            # 比较棋子数
            player_tile = countTile(tep_board, PLAYER_NUM)
            computer_tile = countTile(tep_board, COMPUTER_NUM)
            if computer_tile > player_tile:
                return True
            return False

        if depth > 32:  # 遍历深度
            return eval_board(tep_board)
        turn_positions = possible_positions(tep_board, tile)
        # 查看是否可以在这个位置下棋
        if len(turn_positions) == 0:
            if tile == COMPUTER_NUM:
                neg_turn = PLAYER_NUM
            else:
                neg_turn = COMPUTER_NUM

            neg_turn_positions = possible_positions(tep_board, neg_turn)

            if len(neg_turn_positions) == 0:
                return eval_board(tep_board)
            else:
                tile = neg_turn
                turn_positions = neg_turn_positions

        # 随机放置一个棋子
        temp = turn_positions[random.randrange(0, len(turn_positions))]
        updateBoard(tep_board, tile, temp[0], temp[1])

        # 转换轮次
        if tile == COMPUTER_NUM:
            tile = PLAYER_NUM
        else:
            tile = COMPUTER_NUM

        return find_playout(tep_board, tile, depth=depth + 1)

    def expand(tep_board, tile):
        # 将所有可以下的位置参数扩展为名字、次数、奖励、子节点
        positions = possible_positions(tep_board, tile)
        result = []
        for temp in positions:
            result.append((temp, 0, 0, []))
        return result

    def find_path(root, total_playout):
        current_path = []
        child = root
        parent_playout = total_playout  # 总次数
        isMCTSTurn = True

        while True:
            if len(child) == 0:
                break
            maxidxlist = [0]
            cidx = 0
            if isMCTSTurn:
                maxval = -1
            else:
                maxval = 2

            for n_tuple in child:
                parent, t_playout, reward, t_childrens = n_tuple


                if isMCTSTurn:  # 为真，电脑找最大值
                    cval = ucb1(n_tuple, parent_playout, 0.1)

                    if cval >= maxval:
                        if cval == maxval:
                            maxidxlist.append(cidx)
                        else:
                            maxidxlist = [cidx]
                            maxval = cval
                else:
                    cval = ucb1(n_tuple, parent_playout, -0.1)

                    if cval <= maxval:
                        if cval == maxval:
                            maxidxlist.append(cidx)
                        else:
                            maxidxlist = [cidx]
                            maxval = cval

                cidx += 1

            # 随机进行下棋，扩展
            maxidx = maxidxlist[random.randrange(0, len(maxidxlist))]
            parent, t_playout, reward, t_childrens = child[maxidx]
            current_path.append(parent)
            parent_playout = t_playout
            child = t_childrens
            isMCTSTurn = not isMCTSTurn

        return current_path

    root = expand(board, COMPUTER_NUM)
    current_board = Init_Board()
    current_board2 = Init_Board()
    start_time = time.time()

    for loop in range(0, 5000):
        if (time.time() - start_time) >= MAX_THINK_TIME:
            break


        current_path = find_path(root, loop)

        tile = COMPUTER_NUM
        for temp in current_path:
            updateBoard(current_board, tile, temp[0], temp[1])
            if tile == COMPUTER_NUM:
                tile = PLAYER_NUM
            else:
                tile = COMPUTER_NUM


        isWon = find_playout(current_board2, tile)


        child = root
        for temp in current_path:
            idx = 0
            for n_tuple in child:
                parent, t_playout, reward, t_childrens = n_tuple
                if temp[0] == parent[0] and temp[1] == parent[1]:
                    break
                idx += 1

            if temp[0] == parent[0] and temp[1] == parent[1]:
                t_playout += 1
                if isWon:
                    reward += 1
                if t_playout >= 5 and len(t_childrens) == 0:
                    t_childrens = expand(current_board, tile)

                child[idx] = (parent, t_playout, reward, t_childrens)

            child = t_childrens


    max_avg_reward = -1
    mt_result = (0, 0)
    for n_tuple in root:
        parent, t_playout, reward, t_childrens = n_tuple
        if (t_playout > 0) and (reward / t_playout > max_avg_reward):
            mt_result = parent
            max_avg_reward = reward / t_playout

    return mt_result


total = []
color = "#000000"


class ReversiBoard(Canvas):
    """创建一个画布组件"""
    bianchang = 52
    bianyuan = 5
    board = Init_Board()
    validBoard = True
    isPayerTurn = True



    def __init__(self, master=None):
        """设置棋盘样式，监听下棋"""
        super().__init__(master)
        self.master = master
        width = BOARD_SIZE * self.bianchang
        cv = Canvas.__init__(self, master, relief=SOLID, bd=4,
                             width=width, height=width, cursor="arrow")

        self.bind("<Button-1>", self.put_stones)
        """建立棋盘棋格"""
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                color = "#FFB6C1"
                x0 = i * self.bianchang + self.bianyuan
                y0 = j * self.bianchang + self.bianyuan
                self.create_rectangle(x0, y0, x0 + self.bianchang,
                                      y0 + self.bianchang, fill=color, width=1)
        self.refresh()

    def put_stones(self, event):
        """是否游戏结束"""
        if not self.validBoard:
            self.validBoard = True
            self.board = Init_Board()
            self.isPayerTurn = True



        # 电脑下棋
        if not self.isPayerTurn:
            return
        # 玩家下棋
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        # 获得坐标
        i = int(x / self.bianchang)
        j = int(y / self.bianchang)
        if self.board[i][j] != 0 or updateBoard(self.board, PLAYER_NUM, i, j, check_only=True) == 0:
            return

        updateBoard(self.board, PLAYER_NUM, i, j)
        self.refresh()

        self.after(100, self.AI_move)

    def AI_move(self):
        """电脑下棋"""
        while True:
            player_possible = len(possible_positions(self.board, PLAYER_NUM))
            mcts_possible = len(possible_positions(self.board, COMPUTER_NUM))
            if mcts_possible == 0:
                break

            start = time.time()
            qizi_position = mctsNextPosition(self.board)
            end = time.time()
            one_time = end - start
            print("Computer position:", qizi_position)
            print("Step time:", format(one_time, '.4f'), "s")
            total.append(one_time)  # 总耗时
            updateBoard(self.board, COMPUTER_NUM, qizi_position[0], qizi_position[1])
            self.refresh()

            player_possible = len(possible_positions(self.board, PLAYER_NUM))
            mcts_possible = len(possible_positions(self.board, COMPUTER_NUM))
            if mcts_possible == 0 or player_possible > 0:
                break

        if player_possible == 0 and mcts_possible == 0:
            self.showResult()
            self.validBoard = False

        self.isPayerTurn = True

    def refresh(self):
        """每次更新需要被翻转的棋子"""
        global color
        """遍历所有棋格"""
        a=possible_positions(self.board, PLAYER_NUM)

        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                x0 = i * self.bianchang + self.bianyuan
                y0 = j * self.bianchang + self.bianyuan
                if (i, j) in a:
                    self.create_oval(x0 + 2, y0 + 2, x0 + self.bianchang - 2, y0 + self.bianchang - 2, fill='#00DD00',
                                     width=0)
                if self.board[i][j] == 0:
                    continue
                if self.board[i][j] == PLAYER_NUM:
                    color = "#000000"
                if self.board[i][j] == COMPUTER_NUM:
                    color = "#ffffff"
                """构造黑白棋子"""
                self.create_oval(x0 + 2, y0 + 2, x0 + self.bianchang - 2, y0 + self.bianchang - 2, fill=color, width=0)

    def showResult(self):
        """计算总的棋子数目"""
        player_qizi = countTile(self.board, PLAYER_NUM)
        mcts_qizi = countTile(self.board, COMPUTER_NUM)

        if player_qizi > mcts_qizi:
            tkinter.messagebox.showinfo('游戏结束', "你获胜了")

        elif player_qizi == mcts_qizi:
            tkinter.messagebox.showinfo('游戏结束', "平局")

        else:
            tkinter.messagebox.showinfo('游戏结束', "你失败了")
        print("总耗时 %.5f" % sum(total))



class Reversi(Frame):
    """创建一个Frame框架"""

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master.title("JL21010001 张笑一")
        self.l_title1 = Label(self, text='Black and White Chess', font=('Times', '24', ('italic', 'bold')), fg='#FFB6C1',
                              bg='#EEE8AA', width=20)
        self.l_title1.pack(padx=10, pady=10)
        self.f_board = ReversiBoard(self)
        self.f_board.pack(padx=10, pady=10)


if __name__ == '__main__':
    root = Tk()
    root.geometry('800x600')
    html_gif = PhotoImage(file="./images/8.png")
    label = Label(root, image=html_gif)
    label.place(x=0, y=0)
    # 建标签
    label = Label(root, bg='pink', height=4, width=20, font=('Times', '12', ('italic', 'bold')), text='JL21010001 张笑一')
    label.place(x=30, y=50)
    var = StringVar()
    label = Label(root, bg='pink', height=4, width=18, font=('Times', '12', ('italic', 'bold')), text='select mode')
    label.place(x=30, y=140)


    def print_selection():
        label.config(text='you have selected' + var.get())


    # 设置模式难度
    r1 = Radiobutton(root, text='low', variable=var, value='low', command=print_selection)
    r2 = Radiobutton(root, text='middle', variable=var, value='middle', command=print_selection)
    r3 = Radiobutton(root, text='high', variable=var, value='high', command=print_selection)
    r1.place(x=30, y=220)
    r2.place(x=30, y=240)
    r3.place(x=30, y=260)

    app = Reversi(master=root)
    app.place(x=360, y=0)
    app.mainloop()
