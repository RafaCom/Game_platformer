""" Должны вылетать из бомб монетки """

import math
import random
import time

from array import array
from dataclasses import dataclass
import arcade.gl
import arcade
import arcade.gui


TITLE = 'Game'

SPRITE_IMAGE_SIZE = 128

SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_TILES = 0.5

SPRITE_SIZE = int(SPRITE_IMAGE_SIZE * SPRITE_SCALING_PLAYER)

SCREEN_GRID_WIDTH = 20
SCREEN_GRID_HEIGHT = 18

WIDTH = SPRITE_SIZE * SCREEN_GRID_WIDTH
HEIGHT = SPRITE_SIZE * SCREEN_GRID_HEIGHT

GRAVITY = 1500

DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.4

PLAYER_FRICTION = 1.0
WALL_FRICTION = 0.8
DYNAMIC_ITEM_FRICTION = 0.8

PLAYER_MASS = 2.0

PLAYER_MAX_HORIZONTAL_SPEED = 450
PLAYER_MAX_VERTICAL_SPEED = 1700

PLAYER_MOVE_FORCE_ON_GROUND = 6000

PLAYER_MOVE_FORCE_IN_AIR = 900
PLAYER_JUMP_IMPULSE = 1500

DEAD_ZONE = 0.1

RIGHT_FACING = 0
LEFT_FACING = 1

DISTANCE_TO_CHANGE_TEXTURE = 20

AMBIENT_COLOR = (30, 30, 30)

PARTICLE_COUNT = 300
MIN_FADE_TIME = .25
MAX_FADE_TIME = 1.5

simple_level = False

class MyGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.music_play = False
        self.spike_1 = None
        self.spike = None
        self.enemy_list = None
        self.window.set_mouse_visible(False)

        self.burst_list = []

        self.program = self.window.ctx.load_program(
            vertex_shader='vertex_shader_v4.glsl',
            fragment_shader='fragment_shader.glsl'
        )

        self.window.ctx.enable_only(self.window.ctx.BLEND)

        self.score = 0
        self.score_text = None

        self.life = 2
        self.life_text = None

        self.music_text = None

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.bg_tex_coin = arcade.load_texture(':resources:images/items/coinGold.png')

        arcade.set_background_color(arcade.color.GRAY_ASPARAGUS)

        self.bg_color = arcade.color.AFRICAN_VIOLET

        self.status = True

        self.scene = None
        self.player_sprite = None
        self.tablet = None
        self.block = None
        self.trampoline = None
        self.spikes_list = []

        self.right_pressed = False
        self.left_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        self.physics_engine = None

        self.camera = arcade.Camera(WIDTH, HEIGHT)

        self.collision_bomb = None
        self.sound_game_over = None
        self.sound_win = None
        self.sound_jump = None
        self.sound_coins = None
        self.sound = None
        self.music = None

        self.light_layer = None
        self.player_light = None
        self.coins_light = None
        self.torch_light = None

        # self.pause = PauseView()
        self.game_over = GameOverView()
        self.game_win = GameWin()
        # self.button_pause = None

    def setup(self):
        self.scene = arcade.Scene()

        map_name = ':resources:tiled_maps/map_with_ladders.json'
        map_name_with_bombs = ':resources:tiled_maps/level_1.json'

        tile_map = arcade.load_tilemap(map_name, SPRITE_SCALING_TILES)

        self.scene.add_sprite_list('Background', sprite_list=tile_map.sprite_lists['Background'])
        self.scene.add_sprite_list('Platforms', sprite_list=tile_map.sprite_lists['Platforms'])
        self.scene.add_sprite_list('Moving Platforms', sprite_list=tile_map.sprite_lists['Moving Platforms'])
        self.scene.add_sprite_list('Coins', sprite_list=tile_map.sprite_lists['Coins'])

        tile_map_with_bombs = arcade.load_tilemap(map_name_with_bombs, SPRITE_SCALING_TILES)


        self.player_sprite = Player()
        self.scene.add_sprite('Player', self.player_sprite)

        if not simple_level:
            # self.spike_1 = arcade.Sprite(':resources:images/tiles/spikes.png', scale=0.7)
            # self.spike_1.center_x = 770
            # self.spike_1.center_y = 685
            # self.scene.add_sprite('Enemy', self.spike_1)
            #
            # self.spike = arcade.Sprite(':resources:images/tiles/spikes.png', scale=0.7)
            # self.spike.center_x = 408
            # self.spike.center_y = 108
            # self.scene.add_sprite('Enemy', self.spike)

            self.scene.add_sprite_list('Enemy', sprite_list=tile_map_with_bombs.sprite_lists['Bombs'])

            # self.scene["Enemy"][0].center_x = 400
            # self.scene["Enemy"][0].center_y = 685

            self.scene["Enemy"][1].center_x = 408
            self.scene["Enemy"][1].center_y = 96

            self.scene["Enemy"][2].center_x = 776
            self.scene["Enemy"][2].center_y = 672

            # self.enemy_list = arcade.SpriteList()
            # self.enemy_list.append(self.spike)
            # self.enemy_list.append(self.spike_1)
            # self.scene.add_sprite_list('Enemy', self.enemy_list)


        self.block = arcade.Sprite(':resources:images/tiles/dirtHalf.png', scale=0.5)
        self.block.center_x = 800
        self.block.center_y = 800
        self.scene.add_sprite('Platforms', self.block)

        damping = DEFAULT_DAMPING
        gravity = (0, -GRAVITY)

        self.physics_engine = arcade.PymunkPhysicsEngine(damping=damping, gravity=gravity)

        self.physics_engine.add_sprite(self.player_sprite, friction=PLAYER_FRICTION, mass=PLAYER_MASS,
                                       moment=arcade.PymunkPhysicsEngine.MOMENT_INF, collision_type="Player",
                                       max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
                                       max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED)
        self.physics_engine.add_sprite_list(self.scene['Platforms'],
                                            friction=WALL_FRICTION,
                                            collision_type="Wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)
        self.physics_engine.add_sprite_list(self.scene['Moving Platforms'],
                                            friction=WALL_FRICTION,
                                            collision_type="Wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        self.sound = arcade.load_sound('music.wav')
        if not self.music_play:
            # self.music = arcade.play_sound(self.sound, volume=0.1, looping=True)
            self.music = self.sound.play(volume=0.1, loop=True)
            self.music_play = True
        self.sound_game_over = arcade.load_sound(':resources:sounds/gameover2.wav')
        self.sound_win = arcade.load_sound(':resources:sounds/upgrade1.wav')
        self.sound_jump = arcade.load_sound(':resources:sounds/jump1.wav')
        self.sound_coins = arcade.load_sound(':resources:sounds/coin5.wav')
        self.collision_bomb = arcade.load_sound(':resources:sounds/hurt2.wav')

        self.trampoline = arcade.Sprite(':resources:images/tiles/switchGreen.png', 0.5)
        self.scene.add_sprite_list('Trampoline')

    def on_draw(self):
        self.clear()
        # with self.light_layer:
        self.scene.draw()
        # self.light_layer.draw(ambient_color=AMBIENT_COLOR)

        self.music_text = arcade.gui.UILabel(20, 0 ,
                                             text=str(self.score), font_size=20, text_color=arcade.color.YELLOW)

        self.score_text = arcade.gui.UILabel(20, HEIGHT - 50,
                                             text=str(self.score), font_size=20, text_color=arcade.color.YELLOW)
        if not simple_level:
            self.life_text = arcade.gui.UILabel(WIDTH - 130, HEIGHT - 50,
                                                text=f"Жизнь: {str(self.life)}", font_size=20, text_color=arcade.color.RED)
            self.manager.add(self.life_text)

        self.manager.add(self.score_text)


        self.manager.draw()
        self.manager.remove(self.score_text)
        self.manager.remove(self.life_text)

        self.window.ctx.point_size = 2 * self.window.get_pixel_ratio()

        for burst in self.burst_list:
            self.program['time'] = time.time() - burst.start_time
            burst.vao.render(self.program, mode=self.window.ctx.POINTS)

        # self.camera.use()

    def collision_coin(self, x, y):
        def _gen_initial_data(initial_x, initial_y):
            for i in range(PARTICLE_COUNT):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(0.0, 0.7)
                dx = math.sin(angle) * speed
                dy = math.cos(angle) * speed
                red = random.uniform(0.5, 1.0)
                green = random.uniform(0, red)
                blue = 0  # random.uniform(0.5, 1.0)
                fade_rate = random.uniform(1 / MAX_FADE_TIME, 1 / MIN_FADE_TIME)
                yield initial_x
                yield initial_y
                yield dx
                yield dy
                yield red
                yield green
                yield blue
                yield fade_rate

        x2 = x / WIDTH * 2 - 1
        y2 = y / HEIGHT * 2 - 1
        initial_data = _gen_initial_data(x2, y2)

        buffer = self.window.ctx.buffer(data=array('f', initial_data))
        buffer_description = arcade.gl.BufferDescription(
            buffer, '2f 2f 3f f',
            ['in_pos', 'in_vel', 'in_color', 'in_fade_rate']
        )
        vao = self.window.ctx.geometry([buffer_description])

        burst = Burst(buffer=buffer, vao=vao, start_time=time.time())
        self.burst_list.append(burst)

    def update(self, delta_time: float):
        if self.score < 11:
            if self.status and self.life != 0 and self.player_sprite.top > 0:
                self.physics_engine.step()
                is_on_ground = self.physics_engine.is_on_ground(self.player_sprite)
                if self.left_pressed and not self.right_pressed:
                    if is_on_ground:
                        force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
                    else:
                        force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
                    self.physics_engine.apply_force(self.player_sprite, force)
                    self.physics_engine.set_friction(self.player_sprite, 0)
                elif self.right_pressed and not self.left_pressed:
                    if is_on_ground:
                        force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
                    else:
                        force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
                    self.physics_engine.apply_force(self.player_sprite, force)
                    self.physics_engine.set_friction(self.player_sprite, 0)
                else:
                    self.physics_engine.set_friction(self.player_sprite, 1.0)

                # self.center_camera_to_player()

                for coin in self.scene['Coins']:
                    collision = arcade.check_for_collision(self.player_sprite, coin)
                    if collision:
                        self.score += 1
                        arcade.play_sound(self.sound_coins, volume=0.3)
                        self.collision_coin(coin.center_x, coin.center_y)
                        coin.kill()

                # for trampoline in self.scene['Trampoline']:
                #     collision_trampoline = arcade.check_for_collision(self.player_sprite, trampoline)
                #     if collision_trampoline:
                #         impulse = (0, PLAYER_JUMP_IMPULSE * 1.0)
                #         self.physics_engine.apply_impulse(self.player_sprite, impulse)

                if not simple_level:
                    # for spike in self.scene['Enemy']:
                    #     collision = arcade.check_for_collision(self.player_sprite, self.spike)
                    #     if collision:
                    #         self.collision_coin(WIDTH - 20, HEIGHT)
                    #         self.life -= 1
                    #         self.spike.kill()
                    #         arcade.play_sound(self.collision_bomb, volume=0.5)
                    #
                    #     collision = arcade.check_for_collision(self.player_sprite, self.spike_1)
                    #     if collision:
                    #         self.collision_coin(WIDTH - 20, HEIGHT)
                    #         self.life -= 1
                    #         self.spike_1.kill()
                    #         arcade.play_sound(self.collision_bomb, volume=0.5)

                        for bomb in self.scene['Enemy']:
                            collision_bomb = arcade.check_for_collision(self.player_sprite, bomb)
                            if collision_bomb:
                                self.collision_coin(WIDTH - 20, HEIGHT)
                                self.life -= 1
                                self.collision_coin(bomb.center_x, bomb.center_y)
                                # if self.life != 0:
                                #     self.trampoline.center_x = bomb.center_x
                                #     self.trampoline.center_y = bomb.center_y
                                #     self.scene.add_sprite('Trampoline', self.trampoline)
                                bomb.kill()
                                arcade.play_sound(self.collision_bomb, volume=0.5)

                if self.player_sprite.bottom <= 50:
                    arcade.play_sound(self.sound_game_over)
                    if self.music_play:
                        arcade.stop_sound(self.music)
                        self.music_play = False
                    self.player_sprite.kill()
                    self.status = False
                    self.game_over.setup()
                    self.window.show_view(self.game_over)

                # self.player_light.position = self.player_sprite.position
                temp_list = self.burst_list.copy()
                for burst in temp_list:
                    if time.time() - burst.start_time > MAX_FADE_TIME:
                        self.burst_list.remove(burst)

            else:
                if self.music_play:
                    arcade.stop_sound(self.music)
                    self.music_play = False
                arcade.play_sound(self.sound_game_over, volume=0.3)
                self.game_over.setup()
                self.window.show_view(self.game_over)

        else:
            arcade.play_sound(self.sound_win)
            if self.music_play:
                arcade.stop_sound(self.music)
                self.music_play = False
            self.player_sprite.kill()
            self.status = False
            self.game_win.setup()
            self.window.show_view(self.game_win)

    def on_key_press(self, symbol: int, modifiers: int):
        if self.status:
            if symbol == arcade.key.LEFT or symbol == arcade.key.A:
                self.left_pressed = True
            elif symbol == arcade.key.RIGHT or symbol == arcade.key.D:
                self.right_pressed = True
            elif symbol == arcade.key.UP or symbol == arcade.key.W:
                self.up_pressed = True
                if self.physics_engine.is_on_ground(self.player_sprite):
                    impulse = (0, PLAYER_JUMP_IMPULSE)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                    arcade.play_sound(self.sound_jump, volume=0.3)
            elif symbol == arcade.key.DOWN or symbol == arcade.key.S:
                self.down_pressed = True
            elif symbol == arcade.key.ESCAPE:
                if self.music_play:
                    arcade.stop_sound(self.music)
                    self.music_play = False
                menu_view = MenuView()
                self.window.show_view(menu_view)
                menu_view.setup()
            elif symbol == arcade.key.SPACE:
                if self.music_play:
                    self.music.pause()
                    self.music_play = False
                else:
                    self.music.play()
                    self.music_play = True

    def on_key_release(self, symbol, modifiers):
        if self.status:
            if symbol == arcade.key.LEFT or symbol == arcade.key.A:
                self.left_pressed = False
            elif symbol == arcade.key.RIGHT or symbol == arcade.key.D:
                self.right_pressed = False

    # def center_camera_to_player(self):
    #     window_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
    #     window_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 2)
    #
    #     if window_center_x < 0:
    #         window_center_x = 0
    #     if window_center_y < 0:
    #         window_center_y = 0
    #     player_centered = window_center_x, window_center_y
    #     self.camera.move_to(player_centered)


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__(':resources:images/animated_characters/robot/robot_idle.png')
        self.center_x = SPRITE_SIZE * 2
        self.center_y = SPRITE_SIZE * 2

        main_path = ':resources:images/animated_characters/robot/robot'

        self.idle_texture_pair = self.load_texture_pair(f'{main_path}_idle.png')
        self.jump_texture_pair = self.load_texture_pair(f'{main_path}_jump.png')
        self.fall_texture_pair = self.load_texture_pair(f'{main_path}_fall.png')

        self.walk_textures = []
        for i in range(8):
            texture = self.load_texture_pair(f'{main_path}_walk{i}.png')
            self.walk_textures.append(texture)

        self.texture = self.idle_texture_pair[0]

        self.hit_box = self.texture.hit_box_points

        self.character_face_direction = RIGHT_FACING

        self.cur_texture = 0

        self.x_odometer = 0

    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        if dx < DEAD_ZONE and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif dx > DEAD_ZONE and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        is_on_ground = physics_engine.is_on_ground(self)

        self.x_odometer += dx

        if not is_on_ground:
            if dy > DEAD_ZONE:
                self.texture = self.jump_texture_pair[self.character_face_direction]
                return
            if dy < DEAD_ZONE:
                self.texture = self.fall_texture_pair[self.character_face_direction]
                return

        if abs(dx) <= DEAD_ZONE:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        if abs(self.x_odometer) > DISTANCE_TO_CHANGE_TEXTURE:
            self.x_odometer = 0

            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
            self.texture = self.walk_textures[self.cur_texture][self.character_face_direction]

    @staticmethod
    def load_texture_pair(filename):
        return [
            arcade.load_texture(filename),
            arcade.load_texture(filename, flipped_horizontally=True)
        ]


@dataclass
class Burst:
    buffer: arcade.gl.Buffer
    vao: arcade.gl.Geometry
    start_time: float


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.window.set_mouse_visible(True)

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.buttons_box_menu = arcade.gui.UIBoxLayout()
        self.manager.add(arcade.gui.UIAnchorWidget(
            anchor_x='center_x',
            anchor_y='center_y',
            child=self.buttons_box_menu)
        )

        text = 'Соберите все монетки и флажки для победы!'

        ui_text_label = arcade.gui.UITextArea(text=text, width=920, height=60,
                                              font_size=32,
                                              font_name="Arial")
        self.buttons_box_menu.add(ui_text_label.with_space_around(bottom=15))

        start_button = arcade.gui.UIFlatButton(text='Старт', width=300)
        self.buttons_box_menu.add(start_button.with_space_around(bottom=15))
        start_button.on_click = self.on_click_start

        setting_button = arcade.gui.UIFlatButton(text="Настройки", width=300)
        self.buttons_box_menu.add(setting_button.with_space_around(bottom=15))

        quit_button = arcade.gui.UIFlatButton(text='Выход', width=300)
        self.buttons_box_menu.add(quit_button.with_space_around(bottom=15))

        @quit_button.event('on_click')
        def on_click_quit(event):
            self.window.close()

        @setting_button.event('on_click')
        def on_click_setting(event):
            setting_view = Setting()
            setting_view.setup()
            self.window.show_view(setting_view)

    def setup(self):
        pass

    def on_click_start(self, event):
        game_view = MyGame()
        game_view.setup()
        self.window.show_view(game_view)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.AMAZON)

    def on_draw(self):
        self.clear()
        self.manager.draw()


class GameOverView(arcade.View):
    def __init__(self):
        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.buttons_box_gameover = arcade.gui.UIBoxLayout()
        self.manager.add(arcade.gui.UIAnchorWidget(
            anchor_x='center_x',
            anchor_y='center_y',
            child=self.buttons_box_gameover)
        )

        text = 'Вы проиграли!'

        ui_text_label = arcade.gui.UITextArea(text=text, width=390, height=60,
                                              font_size=42,
                                              font_name="Arial")
        self.buttons_box_gameover.add(ui_text_label.with_space_around(bottom=15))

        restart_button = arcade.gui.UIFlatButton(text='Заново', width=300)
        self.buttons_box_gameover.add(restart_button.with_space_around(bottom=15))
        restart_button.on_click = self.on_click_restart

        setting_button = arcade.gui.UIFlatButton(text="Настройки", width=300)
        self.buttons_box_gameover.add(setting_button.with_space_around(bottom=15))

        # quit_button = arcade.gui.UIFlatButton(text='Выход', width=300)
        # self.buttons_box_gameover.add(quit_button.with_space_around(bottom=15))

        # @quit_button.event('on_click')
        # def on_click_quit(event):
        #     self.window.close()

        @setting_button.event('on_click')
        def on_click_setting(event):
            setting_view = Setting()
            setting_view.setup()
            self.window.show_view(setting_view)

    def on_click_restart(self, event):
        game_view = MyGame()
        game_view.setup()
        self.window.show_view(game_view)

    def setup(self):
        self.window.set_mouse_visible(True)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.ANTIQUE_BRASS)
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        self.clear()
        self.manager.draw()


class GameWin(arcade.View):
    def __init__(self):
        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.buttons_box_gameover = arcade.gui.UIBoxLayout()
        self.manager.add(arcade.gui.UIAnchorWidget(
            anchor_x='center_x',
            anchor_y='center_y',
            child=self.buttons_box_gameover)
        )

        text = 'Вы выиграли!'

        ui_text_label = arcade.gui.UITextArea(text=text, width=357, height=60,
                                              font_size=42,
                                              font_name="Arial")
        self.buttons_box_gameover.add(ui_text_label.with_space_around(bottom=15))

        restart_button = arcade.gui.UIFlatButton(text='Заново', width=300)
        self.buttons_box_gameover.add(restart_button.with_space_around(bottom=15))
        restart_button.on_click = self.on_click_restart

        setting_button = arcade.gui.UIFlatButton(text="Настройки", width=300)
        self.buttons_box_gameover.add(setting_button.with_space_around(bottom=15))

        quit_button = arcade.gui.UIFlatButton(text='Выход', width=300)
        self.buttons_box_gameover.add(quit_button.with_space_around(bottom=15))

        @quit_button.event('on_click')
        def on_click_quit(event):
            self.window.close()

        @setting_button.event('on_click')
        def on_click_setting(event):
            setting_view = Setting()
            setting_view.setup()
            self.window.show_view(setting_view)

    def on_click_restart(self, event):
        game_view = MyGame()
        game_view.setup()
        self.window.show_view(game_view)

    def setup(self):
        self.window.set_mouse_visible(True)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLUE_GRAY)
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        self.clear()
        self.manager.draw()


class Setting(arcade.View):
    def __init__(self):
        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.buttons_box_gameover = arcade.gui.UIBoxLayout()
        self.manager.add(arcade.gui.UIAnchorWidget(
            anchor_x='center_x',
            anchor_y='center_y',
            child=self.buttons_box_gameover)
        )

        text = 'Настройки!'

        ui_text_label = arcade.gui.UITextArea(text=text, width=290, height=60,
                                              font_size=42,
                                              font_name="Arial")
        self.buttons_box_gameover.add(ui_text_label.with_space_around(bottom=15))

        simple_button = arcade.gui.UIFlatButton(text="Легкий уровень", width=300)
        self.buttons_box_gameover.add(simple_button.with_space_around(bottom=15))

        hard_button = arcade.gui.UIFlatButton(text='Сложный уровень', width=300)
        self.buttons_box_gameover.add(hard_button.with_space_around(bottom=15))

        back_button = arcade.gui.UIFlatButton(text='Главное меню', width=300)
        self.buttons_box_gameover.add(back_button.with_space_around(bottom=15))
        back_button.on_click = self.on_click_back

        @hard_button.event('on_click')
        def on_click_hard(event):
            global simple_level
            simple_level = False
            game_view = MyGame()
            game_view.setup()
            self.window.show_view(game_view)

        @simple_button.event('on_click')
        def on_click_simple(event):
            global simple_level
            simple_level = True
            game_view = MyGame()
            game_view.setup()
            self.window.show_view(game_view)

    def on_click_back(self, event):
        menu_view = MenuView()
        self.window.show_view(menu_view)
        menu_view.setup()

    def setup(self):
        self.window.set_mouse_visible(True)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLUE_GRAY)
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        self.clear()
        self.manager.draw()


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    menu_view = MenuView()
    window.show_view(menu_view)
    menu_view.setup()
    arcade.run()


if __name__ == "__main__":
    main()
