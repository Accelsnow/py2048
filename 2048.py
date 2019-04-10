import math
import os
import random
import threading

import pyHook
import pygame
import pythoncom
import wx


class BoardPanel(wx.Panel):
    __COLOR_COLLECTION = ["#f5ecce", "#f5da81", "#facc2e", "#fe9a2e", "#ff8000",
                          "#df7401", "#ff4000", "#ff0000",
                          "#df0101", "#b40404", "#8A0808", "#610B0B", "#3B170B"]

    def __init__(self, parent, identifier, pos, size, style, name, border_size):
        wx.Panel.__init__(self, parent, identifier, pos, size, style, name)
        self.__num = 1
        self.__prev_num = self.__num
        self.__label = wx.StaticText(self, wx.ID_ANY, "", style=wx.ALIGN_CENTER)
        self.__label.SetFont(
            wx.Font(18, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL))

        self.__dim = size[1]
        self.__label_height = self.__label.GetSize()[1]
        self.__border_size = border_size
        self.__label.SetPosition((self.__dim / 2 - border_size * 2,
                                  self.__dim / 2 - self.__label_height / 2))
        self.refresh_display()

    def change_num(self, number):
        if number == 1 or (number % 2 == 0 and number <= 2 ** 17):
            self.__num = number
            self.refresh_display()
            return 1
        else:
            raise ValueError

    def refresh_display(self):
        if self.__num == 1:
            self.__label.SetLabel("")
        else:
            self.__label.SetLabel(str(self.__num))

        index = int(math.log(self.__num, 2))
        if index < len(self.__COLOR_COLLECTION):
            self.SetBackgroundColour(self.__COLOR_COLLECTION[index])
        else:
            self.SetBackgroundColour(
                self.__COLOR_COLLECTION[len(self.__COLOR_COLLECTION) - 1])

        if index >= 10:
            self.__label.SetForegroundColour("white")

        self.__label.SetPosition((self.__dim / 2 - self.__border_size * (
                    2 + 3 * (len(self.__label.GetLabel()) - 1)),
                                  self.__dim / 2 - self.__label_height / 2))
        self.Refresh()

    def roll_back(self):
        self.__num = self.__prev_num
        self.refresh_display()

    def has_changed(self):
        if self.__num == self.__prev_num:
            return False
        return True

    def set_prev(self):
        self.__prev_num = self.__num

    def get_num(self):
        return self.__num


class MusicThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pygame.mixer.init()
        music = pygame.mixer.Sound("bgm.ogg")
        music.play()


class GameFrame(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(400, 100),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        self.CreateStatusBar()
        self.__score = 0
        self.__prev_score = self.__score
        display_width, display_height = wx.GetDisplaySize()

        self.__game_board = [[BoardPanel(self, wx.ID_ANY, wx.DefaultPosition,
                                         (display_height * 0.8 / 9,
                                          display_height * 0.8 / 9),
                                         wx.TAB_TRAVERSAL, "board", 2) for i in
                              range(0, 4)] for j in range(0, 4)]

        self.SetBackgroundColour(wx.NullColour)

        game_menu = wx.Menu()
        game_menu_load = game_menu.Append(wx.ID_OPEN, "Load",
                                          "Load a saved game")
        game_menu_save = game_menu.Append(wx.ID_SAVE, "Save",
                                          "Save current game")
        game_menu.AppendSeparator()
        game_menu_exit = game_menu.Append(wx.ID_EXIT, "Exit",
                                          "Terminate the game")

        menu_bar = wx.MenuBar()
        menu_bar.Append(game_menu, "&Game")
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.__on_load, game_menu_load)
        self.Bind(wx.EVT_MENU, self.__on_save, game_menu_save)
        self.Bind(wx.EVT_MENU, self.__on_exit, game_menu_exit)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.AddStretchSpacer(1.5)
        title_text = wx.StaticText(self, wx.ID_ANY, title, (20, 100))
        title_text.SetFont(wx.Font(18, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL,
                                   wx.FONTWEIGHT_BOLD))
        top_sizer.Add(title_text, 3, wx.ALIGN_CENTER)

        info_sizer = wx.BoxSizer(wx.VERTICAL)
        info_sizer.AddStretchSpacer(2)
        self.__score_text = wx.StaticText(self, wx.ID_ANY, "",
                                          style=wx.ALIGN_CENTER)
        self.__score_text.SetFont(
            wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD))
        info_sizer.Add(self.__score_text, 3.5, wx.EXPAND)

        button_sizer = wx.GridSizer(rows=1, cols=2, hgap=20, vgap=0)
        self.__redo_button = wx.Button(self, -1, "Redo")
        self.__reset_button = wx.Button(self, -1, "Reset")
        self.Bind(wx.EVT_BUTTON, self.__click_redo, self.__redo_button)
        self.Bind(wx.EVT_BUTTON, self.__click_reset, self.__reset_button)
        button_sizer.Add(self.__redo_button, 0, wx.ALIGN_CENTER)
        button_sizer.Add(self.__reset_button, 0, wx.ALIGN_CENTER)

        info_sizer.Add(button_sizer, 2.5, wx.EXPAND)
        info_sizer.AddStretchSpacer(2)

        top_sizer.Add(info_sizer, 4, wx.ALIGN_CENTER)
        top_sizer.AddStretchSpacer(1.5)

        self.__main_sizer = wx.GridBagSizer(hgap=0, vgap=5)
        self.__main_sizer.Add(top_sizer, pos=(0, 0),
                              flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        game_sizer = wx.GridBagSizer(hgap=2, vgap=2)

        for r in range(0, 4):
            for c in range(0, 4):
                game_sizer.Add(self.__game_board[r][c], pos=(r, c),
                               flag=wx.ALL | wx.ALIGN_CENTER, border=2)

        self.__main_sizer.Add(game_sizer, pos=(1, 0),
                              flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        instruction_text = wx.StaticText(self, wx.ID_ANY,
                                         "Swipe to move. 2 + 2 = 4. Reach 2048.",
                                         style=wx.ALIGN_CENTER)
        instruction_text.SetFont(
            wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD))
        self.__main_sizer.Add(instruction_text, pos=(2, 0),
                              flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        self.SetSizer(self.__main_sizer)
        self.SetAutoLayout(1)
        self.__main_sizer.Fit(self)

        self.refresh()
        self.Show(True)

        key_listener = pyHook.HookManager()
        key_listener.KeyDown = self.__key_pressed
        key_listener.HookKeyboard()
        hook_thread = threading.Thread(target=pythoncom.PumpMessages)
        hook_thread.start()

        music_player = MusicThread()
        music_player.start()

        self.__rand_gen()

    def __on_load(self, e):
        confirmation = wx.MessageBox(
            "This will destroy your current game and load the saved game"
            "(if there is any). "
            "Would you like to continue?", "Caution!",
            wx.CANCEL | wx.OK | wx.ICON_QUESTION)
        if confirmation == wx.OK:
            self.__save_current_board()

            try:
                file_open = open("save2048.txt")
                txt_len = len(file_open.read())
                if txt_len > 83 or txt_len < 45:
                    raise ValueError

                row = 0

                for line in file_open:
                    if line.startswith("score "):
                        score_value = int(line[int(line.find(" ") + 1):])

                        if score_value > 3885758 or score_value < 0:
                            raise ValueError
                        else:
                            self.__score = score_value
                        break

                    else:
                        arr = line.split()
                        for col in range(0, 4):
                            self.__game_board[row][col].change_num(
                                int(arr[col]))

                    row = row + 1

                self.refresh()
                file_open.close()
                return 1

            except IOError:
                self.__click_redo(None)
                error = wx.MessageBox("No save found! Would you like to save?",
                                      "ERROR!",
                                      wx.CANCEL | wx.OK | wx.ICON_QUESTION)
                if error == wx.OK:
                    self.__on_save(None)
                return 0

            except(IndexError, ValueError):
                self.__click_redo(None)
                error = wx.MessageBox(
                    "Invalid game save file! Would you like to save?", "ERROR!",
                    wx.CANCEL | wx.OK | wx.ICON_QUESTION)
                if error == wx.OK:
                    self.__on_save(None)
                return 0

        return 0

    def __on_save(self, e):
        confirmation = wx.MessageBox(
            "This will overwrite your previous save(if there is any). "
            "Would you like to continue?", "Caution!",
            wx.CANCEL | wx.OK | wx.ICON_QUESTION)
        if confirmation == wx.OK:
            file_out = open("save2048.txt", 'w')
            for r in range(0, 4):
                for c in range(0, 4):
                    if c == 3:
                        file_out.write(
                            str(self.__game_board[r][c].get_num()) + "\n")
                    else:
                        file_out.write(
                            str(self.__game_board[r][c].get_num()) + " ")

            file_out.write("score " + str(self.__score))
            file_out.close()
            return 1
        return 0

    def __on_exit(self, e):
        self.Close(True)

    def get_score(self):
        return self.__score

    def __click_reset(self, e):
        confirmation = wx.MessageBox(
            "Do you really want to reset the whole game?", "Caution!",
            wx.CANCEL | wx.OK | wx.ICON_QUESTION)
        if confirmation == wx.OK:
            for r in range(0, 4):
                for c in range(0, 4):
                    self.__game_board[r][c].change_num(1)
                    self.__game_board[r][c].set_prev()

            self.__rand_gen()
            self.refresh()
            return 1
        return 0

    def __click_redo(self, e):
        for r in range(0, 4):
            for c in range(0, 4):
                self.__game_board[r][c].roll_back()
        self.__score = self.__prev_score
        self.refresh()
        return 1

    def __rand_gen(self):
        r = -1
        c = -1
        while (r == -1 and c == -1) or self.__game_board[r][c].get_num() != 1:
            r = random.randint(0, 3)
            c = random.randint(0, 3)
        if random.randint(0, 3) < 3:
            target = 2
        else:
            target = 4
        self.__game_board[r][c].change_num(target)

    def refresh(self):
        self.__score_text.SetLabel("Score: " + str(self.__score))
        self.__main_sizer.Layout()
        self.Refresh()

    def board_has_changed(self):
        for r in range(0, 4):
            for c in range(0, 4):
                if self.__game_board[r][c].has_changed():
                    return True
        return False

    def __save_current_board(self):
        for r in range(0, 4):
            for c in range(0, 4):
                self.__game_board[r][c].set_prev()
        self.__prev_score = self.__score

    def __key_pressed(self, event):
        key = event.Key
        is_valid_key = False

        if key == "Up" or key == "Down" or key == "Left" or key == "Right":
            is_valid_key = True
            self.__save_current_board()

        if key == "Up":
            row = 0
            while row < 3:
                for col in range(0, 4):
                    cur = self.__game_board[row][col]

                    for i in range(1, 4):
                        if row + i < 4:
                            nxt = self.__game_board[row + i][col]
                        else:
                            break

                        if cur.get_num() == 1:
                            if nxt.get_num() != 1:
                                cur.change_num(nxt.get_num())
                                nxt.change_num(1)
                            else:
                                continue
                        else:
                            if nxt.get_num() == 1:
                                continue
                            elif nxt.get_num() == cur.get_num():
                                target = nxt.get_num() * 2
                                cur.change_num(target)
                                nxt.change_num(1)
                                self.__score = self.__score + target
                            else:
                                if i > 1:
                                    self.__game_board[row + 1][col].change_num(
                                        nxt.get_num())
                                    nxt.change_num(1)
                                break

                row = row + 1

        elif key == "Down":
            row = 3
            while row >= 0:
                for col in range(0, 4):
                    cur = self.__game_board[row][col]

                    for i in range(1, 4):
                        if row - i >= 0:
                            nxt = self.__game_board[row - i][col]
                        else:
                            break

                        if cur.get_num() == 1:
                            if nxt.get_num() != 1:
                                cur.change_num(nxt.get_num())
                                nxt.change_num(1)
                            else:
                                continue
                        else:
                            if nxt.get_num() == 1:
                                continue
                            elif nxt.get_num() == cur.get_num():
                                target = nxt.get_num() * 2
                                cur.change_num(target)
                                nxt.change_num(1)
                                self.__score = self.__score + target
                                break
                            else:
                                if i > 1:
                                    self.__game_board[row - 1][col].change_num(
                                        nxt.get_num())
                                    nxt.change_num(1)
                                break

                row = row - 1

        elif key == "Left":
            col = 0
            while col < 4:
                for row in range(0, 4):
                    cur = self.__game_board[row][col]

                    for i in range(1, 4):
                        if col + i < 4:
                            nxt = self.__game_board[row][col + i]
                        else:
                            break

                        if cur.get_num() == 1:
                            if nxt.get_num() != 1:
                                cur.change_num(nxt.get_num())
                                nxt.change_num(1)
                            else:
                                continue
                        else:
                            if nxt.get_num() == 1:
                                continue
                            elif nxt.get_num() == cur.get_num():
                                target = nxt.get_num() * 2
                                cur.change_num(target)
                                nxt.change_num(1)
                                self.__score = self.__score + target
                                break
                            else:
                                if i > 1:
                                    self.__game_board[row][col + 1].change_num(
                                        nxt.get_num())
                                    nxt.change_num(1)
                                break

                col = col + 1

        elif key == "Right":
            col = 3
            while col >= 0:
                for row in range(0, 4):
                    cur = self.__game_board[row][col]

                    for i in range(1, 4):
                        if col - i >= 0:
                            nxt = self.__game_board[row][col - i]
                        else:
                            break

                        if cur.get_num() == 1:
                            if nxt.get_num() != 1:
                                cur.change_num(nxt.get_num())
                                nxt.change_num(1)
                            else:
                                continue
                        else:
                            if nxt.get_num() == 1:
                                continue
                            elif nxt.get_num() == cur.get_num():
                                target = nxt.get_num() * 2
                                cur.change_num(target)
                                nxt.change_num(1)
                                self.__score = self.__score + target
                                break
                            else:
                                if i > 1:
                                    self.__game_board[row][col - 1].change_num(
                                        nxt.get_num())
                                    nxt.change_num(1)
                                break

                col = col - 1

        if is_valid_key and self.board_has_changed():
            self.__rand_gen()
            self.refresh()

        return 1


class GameApp(wx.App):
    def OnInit(self):
        self.__frame = GameFrame(None, "2048")
        self.SetTopWindow(self.__frame)
        return 1

    def OnExit(self):
        os._exit(0)


app = GameApp(False)
app.MainLoop()
