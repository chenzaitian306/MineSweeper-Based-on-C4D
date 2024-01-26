# coding=utf-8
# R2023 edition by wechatID：:czt_306

import c4d
import weakref
import os
import random
from datetime import datetime


def load_bitmap(path):
    path = os.path.join(os.path.dirname(__file__), path)
    bmp = c4d.bitmaps.BaseBitmap()
    if bmp.InitWith(path)[0] != c4d.IMAGERESULT_OK:
        bmp = None
    return bmp


def GetCharacterKeysInput(*args):
    lst = [c4d.KEY_SHIFT, c4d.KEY_CONTROL, c4d.KEY_ALT]
    result = {}
    for char in (n for n in args if n in lst):
        bc = c4d.BaseContainer()
        if not c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, char, bc):
            raise RuntimeError("Failed to poll the keyboard.")
        result[char] = True if bc[c4d.BFM_INPUT_VALUE] == 1 else False
    return result


class Square(object):
    def __init__(self, geUserArea, col, row, isBomb):
        self.parentGeUserArea = weakref.ref(geUserArea)  # A weak reference to the host GeUserArea
        self.GeUserArea = geUserArea
        self.col = col
        self.row = row
        self.isBomb = isBomb
        self.status = 0  # 0:不显示，1：显示小旗子  2：显示安全  3:显示地雷数量 4:地雷
        self.icon_id = {0: None, 1: c4d.Owinddeform, 2: 1028462, 4: c4d.Oexplosion}
        self.bombNum = 0
        self.position = [self.col, self.row]

    def GetAroundId(self):
        lst = []
        for i in range(max(self.col - 1, 0), min(self.col + 2, self.GeUserArea.dialog.col)):
            for j in range(max(self.row - 1, 0), min(self.row + 2, self.GeUserArea.dialog.row)):
                if [i, j] != [self.col, self.row]:
                    lst.append([i, j])
        return lst

    def GetTenAroundId(self):
        lst = []
        for i in range(max(self.col - 1, 0), min(self.col + 2, self.GeUserArea.dialog.col)):
            for j in range(max(self.row - 1, 0), min(self.row + 2, self.GeUserArea.dialog.row)):
                if not (i != self.col and j != self.row):
                    lst.append([i, j])
        return lst

    def drawSquare(self, x1, y1, x2, y2, msg):
        if self.status != 3:
            if self.status != 0:
                bmp = c4d.bitmaps.InitResourceBitmap(self.icon_id[self.status])
                self.GeUserArea.DrawBitmap(bmp, self.col * self.GeUserArea.size,
                                           self.row * self.GeUserArea.size,
                                           self.GeUserArea.size, self.GeUserArea.size, 0, 0, 64, 64,
                                           c4d.BMP_NORMAL | c4d.BMP_ALLOWALPHA)
        else:
            if self.bombNum == 0:
                self.status = 2
            else:
                self.GeUserArea.DrawBitmap(load_bitmap(f'res/icons/yellow_{self.bombNum}.tif'),
                                           self.col * self.GeUserArea.size, self.row * self.GeUserArea.size,
                                           self.GeUserArea.size, self.GeUserArea.size, 0, 0, 64, 64,
                                           c4d.BMP_NORMAL | c4d.BMP_ALLOWALPHA)


class backGroundArea(c4d.gui.GeUserArea):
    def __init__(self, Dialog, doc, size):
        self.dialog = Dialog
        self.doc = doc
        self.size = size
        self.color = c4d.Vector(0.2)
        self.squares = self.InitSquares(2)

    def Message(self, msg, result):
        return super(backGroundArea, self).Message(msg, result)

    def CreateRandomList(self, iter):
        lst = [True] * int(self.dialog.BombNum) + [False] * int(self.dialog.col * self.dialog.row - self.dialog.BombNum)
        for i in range(int(iter)):
            random.shuffle(lst)
        return lst

    def InitSquares(self, iter):
        bombs = self.CreateRandomList(iter)
        lst = []
        for n in range(self.dialog.col * self.dialog.row):
            y = n // self.dialog.col
            x = n % self.dialog.col
            temp = Square(self, x, y, bombs[n])
            lst.append(temp)
        return lst

    def GetSquareByPos(self, x, y):
        n = int(y * self.dialog.col + x)
        return self.squares[n]

    def GetSquareByXY(self, xIn, yIn):
        col = xIn // self.dialog.size
        row = yIn // self.dialog.size
        return int(col), int(row)

    def GetBombNum(self, sq):
        lst = sq.GetAroundId()
        n = 0
        for [x, y] in lst:
            if self.GetSquareByPos(x, y).isBomb:
                n += 1
        return n

    def GetForward(self, col, row):
        sq = self.GetSquareByPos(col, row)
        num = sq.bombNum
        if num == 0:
            sq.status = 2
            lst = sq.GetTenAroundId()
            for [x, y] in lst:
                sub_sq = self.GetSquareByPos(x, y)
                if sub_sq.status == 0:
                    self.GetForward(x, y)
        else:
            sq.status = 3
            return

    def InitBombNum(self):
        for sq in self.squares:
            sq.bombNum = self.GetBombNum(sq)

    def show(self):
        for sq in self.squares:
            sq.bombNum = self.GetBombNum(sq)
            if sq.isBomb:
                sq.status = 4

    def checkDone(self):
        n = 0
        for sq in self.squares:
            if sq.isBomb and sq.status == 1:
                n += 1
        print(f'数量合计：{n}')
        if n == self.dialog.BombNum:
            return True
        else:
            return False

    def DrawMsg(self, x1, y1, x2, y2, msg):
        self.OffScreenOn()
        self.SetClippingRegion(x1, y1, x2, y2)

        self.DrawSetPen(self.color)
        self.DrawRectangle(x1, y1, x2, y2)

        for square in self.squares:
            square.drawSquare(x1, y1, x2, y2, msg)
        # self.show()

        self.DrawSetPen(self.color * 0.6)
        for dx in range(1, self.GetWidth() // self.dialog.size + 1):
            self.DrawLine(self.size * dx, 0, self.size * dx, self.GetHeight())
        for dy in range(1, self.GetHeight() // self.dialog.size + 1):
            self.DrawLine(0, self.size * dy, self.GetWidth(), self.size * dy)
        self.DrawFrame(x1, y1, x2 - 1, y2 - 1, lineWidth=1.0, lineStyle=c4d.LINESTYLE_NORMAL)

    def InputEvent(self, msg):
        self.dialog.Activate(1000)
        if msg[c4d.BFM_INPUT_DEVICE] != c4d.BFM_INPUT_MOUSE:
            return True
        mouseX = msg[c4d.BFM_INPUT_X]
        mouseY = msg[c4d.BFM_INPUT_Y]
        x, y, w, h = self.dialog.GetItemDim(1000).values()

        mouseX -= x
        mouseY -= y
        col, row = self.GetSquareByXY(mouseX, mouseY)
        sq = self.GetSquareByPos(col, row)
        print(col,row)
        if msg[c4d.BFM_INPUT_DEVICE] == c4d.BFM_INPUT_MOUSE and msg[c4d.BFM_INPUT_CHANNEL] == c4d.BFM_INPUT_MOUSELEFT:
            if sq.isBomb:
                # TODO:游戏结束
                sq.status = 4
                self.show()
                self.Redraw()
                # TODO:弹出结束信息
                c4d.gui.MessageDialog(f"游戏结束了！", type=c4d.GEMB_OK)
                self.dialog.Close()
                return True

            if sq.status == 0:
                # TODO:开拓地图区域
                if sq.bombNum == 0:
                    sq.status = 2
                    self.GetForward(col, row)
                else:
                    sq.status = 3

        if msg[c4d.BFM_INPUT_DEVICE] == c4d.BFM_INPUT_MOUSE and msg[c4d.BFM_INPUT_CHANNEL] == c4d.BFM_INPUT_MOUSERIGHT:
            if sq.status == 0:
                sq.status = 1
            elif sq.status == 1:
                sq.status = 0
            else:
                pass
        self.Redraw()
        if self.checkDone():
            end_time = datetime.now()
            delta = end_time - self.dialog.get_time
            seconds = delta.total_seconds()
            bomb = self.dialog.BombNum
            c4d.gui.MessageDialog(f"恭喜你已经完成了一局！\n仅用时{seconds}秒排除了{bomb}个地雷", type=c4d.GEMB_OK)
            self.dialog.Close()
            return True
        return True


class MyDialog(c4d.gui.GeDialog):

    def __init__(self, doc, BombNum, col=30, row=16, size=32):
        self.doc = doc
        self.BombNum = BombNum
        self.col = col
        self.row = row
        self.size = size
        self.width = self.col * self.size
        self.height = self.row * self.size
        self.area = backGroundArea(self, self.doc, self.size)
        self.get_time = datetime.now()
        self.window_width = 0
        self.window_height = 0

    def CreateLayout(self):
        self.SetTitle("扫雷")
        self.AddUserArea(1000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=int(self.width) + self.size * 2,
                         inith=int(self.height / 1.5))
        self.AttachUserArea(self.area, 1000)
        self.GroupEnd()
        return True

    def InitValues(self):
        self.Activate(900)
        self.area.InitBombNum()
        return True

    def Command(self, messageId, msg):
        return True

    def Message(self, msg, result):
        return super(MyDialog, self).Message(msg, result)


class Setting(c4d.gui.GeDialog):
    def __init__(self, doc,myDialog):
        self.doc = doc
        self.myDialog = myDialog

    def CreateLayout(self):
        self.SetTitle("扫雷")
        if self.GroupBegin(1000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=2, rows=4):
            self.GroupBorderSpace(5,5,5,5)
            self.AddStaticText(1001, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=20, inith=15, name='列数：', borderstyle=0)
            self.AddEditNumberArrows(1002, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=70, inith=0)
            self.AddStaticText(1003, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=20, inith=15, name='行数：', borderstyle=0)
            self.AddEditNumberArrows(1004, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=70, inith=0)
            self.AddStaticText(1005, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=20, inith=15, name='元素尺寸：',
                               borderstyle=0)
            self.AddEditNumberArrows(1006, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=70, inith=0)
            self.AddStaticText(1007, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=20, inith=15, name='游戏难度：',
                               borderstyle=0)
            self.AddEditNumberArrows(1008, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, initw=70, inith=0)
            self.SetInt32(1002, 30, min=8, max=110, step=1, tristate=False, min2=8, max2=110)
            self.SetInt32(1004, 16, min=8, max=60, step=1, tristate=False, min2=8, max2=60)
            self.SetInt32(1006, 32, min=16, max=32, step=1, tristate=False, min2=16, max2=32)
            self.SetInt32(1008, 2, min=1, max=10, step=1, tristate=False, min2=1, max2=10)
            self.GroupEnd()
        self.AddDlgGroup(c4d.DLG_OK | c4d.DLG_CANCEL)
        return True

    def Command(self, messageId, msg):
        if messageId == c4d.DLG_OK:
            col = self.GetInt32(1002)
            row = self.GetInt32(1004)
            size = self.GetInt32(1006)
            level = self.GetInt32(1008)
            self.myDialog = MyDialog(self.doc, int(col * row * level / 20), col=col, row=row, size=size)
            self.myDialog.Open(dlgtype=c4d.DLG_TYPE_MODAL, defaultw=int(self.myDialog.width) + 24,xpos=-2,ypos=-2)
            self.Close()
        if messageId == c4d.DLG_CANCEL:
            self.Close()
        return True

class MineSweeper(c4d.plugins.CommandData):
    def __init__(self):
        self.dialog = None
        self.setting = None

    def Execute(self, doc):
        result = GetCharacterKeysInput(c4d.KEY_CONTROL)
        if result[c4d.KEY_CONTROL]:
            self.setting = Setting(doc,self.dialog)
            self.setting.Open(dlgtype=c4d.DLG_TYPE_MODAL,xpos=-2,ypos=-2)
        else:
            self.dialog = MyDialog(doc, int(30 * 16 * 2 / 20), col=30, row=16, size=32)
            self.dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL, defaultw=int(self.dialog.width) + 24)
        return True


if __name__ == '__main__':
    icon_Case = load_bitmap('res/icons/MineSweeper.tif')
    text = 'Click: Easy mode\nCtrl+Click: Set hard mode'
    c4d.plugins.RegisterCommandPlugin(id=1062049, str="MineSweeper v1.0",
                                      help=text,
                                      info=0, dat=MineSweeper(), icon=icon_Case)
