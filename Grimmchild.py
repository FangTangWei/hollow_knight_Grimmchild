import sys
import os
import random
import math
from PyQt5.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu,
                             QAction, QActionGroup, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QUrl
from PyQt5.QtGui import QPixmap, QPainter, QTransform, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

# -------------------- 动画资源加载 --------------------
ANIM_FRAMES = {}

def load_animations(base_dir):
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"目录不存在: {base_dir}")
    name_mapping = {
        'flameball impact': 'flameball_impact',
        'flameball': 'flameball',
        'burst': 'burst',
        'fly': 'fly',
        'turntoidle': 'turntoidle',
        'tele out': 'tele_out',
        'tele in': 'tele_in',
        'wake': 'wake',
        'sleep': 'sleep',
        'shoot': 'shoot',
        'antic': 'antic',
        'idle': 'idle',
    }
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue
        parts = folder.split('.', 1)
        if len(parts) < 2:
            continue
        raw_name = parts[1].strip().lower()
        anim_base = None
        stage = None
        for key in name_mapping:
            if raw_name.startswith(key):
                anim_base = name_mapping[key]
                rest = raw_name[len(key):].strip()
                if rest.isdigit():
                    stage = int(rest)
                break
        if anim_base is None:
            continue
        frames = []
        for file in sorted(os.listdir(folder_path)):
            if file.lower().endswith('.png'):
                try:
                    idx = int(file.split('-')[1])
                    frames.append((idx, os.path.join(folder_path, file)))
                except (IndexError, ValueError):
                    continue
        frames.sort(key=lambda x: x[0])
        pixmaps = [QPixmap(path) for _, path in frames]
        if pixmaps:
            ANIM_FRAMES[(anim_base, stage)] = pixmaps
    print(f"动画加载完成，共 {len(ANIM_FRAMES)} 组")

# -------------------- 音频管理 --------------------
class AudioManager:
    def __init__(self, audio_dir):
        self.audio_dir = audio_dir
        self.audio_enabled = True
        self.bgm_player = None
        self.current_bgm = None
        self.bgm_volume = 100
        self._players = []

        self.sounds = {}
        sound_files = {
            'attack_yelp_1_3': '1Grimmbat_attack_yelp_1~3.mp3',
            'attack_yelp_4': '1Grimmbat_attack_yelp_4.mp3',
            'fireball_yelp_1_3': '2Grimmbat_attack_yelp_1~3.mp3',
            'fireball_yelp_4': '2Grimmbat_attack_yelp_4.mp3',
            'teleport_out': 'grimm_teleport_out.mp3',
            'idle_1_3': 'Grimmbat_idle_1~3.mp3',
            'idle_4': 'Grimmbat_idle_4.mp3',
            'fly_loop': 'grimmchild_fly_loop.mp3',
            'fireball_shoot': 'grimmchild_fireball_shoot.mp3',
            'bgm_grimm': 'Grimm.mp3',
            'bgm_epic': 'Grimm Epic Layer.mp3',
        }
        for key, filename in sound_files.items():
            path = os.path.join(self.audio_dir, filename)
            if os.path.exists(path):
                self.sounds[key] = path
            else:
                print(f"音频文件未找到: {filename}")
        print(f"音频加载完成，共 {len(self.sounds)} 个")

    def _cleanup_player(self, player, status):
        if status == QMediaPlayer.EndOfMedia:
            if player in self._players:
                self._players.remove(player)
            player.deleteLater()

    def play_sound(self, key):
        """播放一次性音效"""
        if not self.audio_enabled or key not in self.sounds:
            return
        player = QMediaPlayer()
        player.setMedia(QMediaContent(QUrl.fromLocalFile(self.sounds[key])))
        player.mediaStatusChanged.connect(
            lambda status, p=player: self._cleanup_player(p, status))
        player.play()
        self._players.append(player)

    def create_loop_player(self, key):
        """创建循环播放器，返回 QMediaPlayer 实例"""
        if key not in self.sounds:
            return None
        player = QMediaPlayer()
        player.setMedia(QMediaContent(QUrl.fromLocalFile(self.sounds[key])))

        def loop(status, p=player):
            if status == QMediaPlayer.EndOfMedia:
                p.setPosition(0)
                p.play()
        player.mediaStatusChanged.connect(loop)
        return player

    def play_bgm(self, key):
        """播放背景音乐"""
        if self.bgm_player:
            self.bgm_player.stop()
            self.bgm_player.deleteLater()
        if key in self.sounds:
            self.bgm_player = QMediaPlayer()
            self.bgm_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.sounds[key])))
            self.bgm_player.setVolume(self.bgm_volume)

            def loop(status):
                if status == QMediaPlayer.EndOfMedia:
                    self.bgm_player.setPosition(0)
                    self.bgm_player.play()
            self.bgm_player.mediaStatusChanged.connect(loop)
            if self.audio_enabled:
                self.bgm_player.play()
            self.current_bgm = key

    def stop_bgm(self):
        if self.bgm_player:
            self.bgm_player.stop()
            self.bgm_player.deleteLater()
            self.bgm_player = None
            self.current_bgm = None

    def set_bgm_volume(self, volume):
        """设置背景音乐音量 0-100"""
        self.bgm_volume = volume
        if self.bgm_player:
            self.bgm_player.setVolume(volume)

    def stop_all(self):
        for p in self._players[:]:
            try:
                p.stop()
            except Exception:
                pass
        self._players.clear()
        if self.bgm_player:
            self.bgm_player.stop()

    def toggle_audio(self):
        """切换音频开关，返回新的状态"""
        self.audio_enabled = not self.audio_enabled
        if not self.audio_enabled:
            self.stop_all()
        else:
            if self.bgm_player and self.current_bgm:
                self.bgm_player.play()
        return self.audio_enabled

# 全局音频管理器
audio_manager = None

# -------------------- 火球 --------------------
class Fireball:
    def __init__(self, start_pos, target_pos, owner=None, speed=12):
        self.pos = QPointF(start_pos)
        self.target_pos = QPointF(target_pos)
        self.owner = owner
        dx = target_pos.x() - start_pos.x()
        dy = target_pos.y() - start_pos.y()
        dist = math.hypot(dx, dy)
        if dist < 1:
            dist = 1
        self.vx = dx / dist * speed
        self.vy = dy / dist * speed
        self.active = True
        self.impacting = False
        self.frames = ANIM_FRAMES.get(('flameball', None), [])
        self.impact_frames = ANIM_FRAMES.get(('flameball_impact', None), [])
        self.frame_idx = 0
        self.timer = 0

        # 播放火球发射音效
        global audio_manager
        if audio_manager is not None and owner is not None:
            if owner.stage <= 3:
                audio_manager.play_sound('fireball_yelp_1_3')
            else:
                audio_manager.play_sound('fireball_yelp_4')
            audio_manager.play_sound('fireball_shoot')

    def update(self):
        if self.impacting:
            self.timer += 1
            if self.timer % 3 == 0:
                self.frame_idx += 1
                if self.frame_idx >= len(self.impact_frames):
                    self.active = False
            return
        self.pos += QPointF(self.vx, self.vy)
        self.timer += 1
        if self.frames and self.timer % 3 == 0:
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        screen = QApplication.primaryScreen().geometry()
        if (self.pos.x() < -100 or self.pos.x() > screen.width() + 100 or
            self.pos.y() < -100 or self.pos.y() > screen.height() + 100):
            self.active = False

    def hit_check(self, pet):
        if not self.active or self.impacting:
            return False
        if pet is self.owner:
            return False
        pet_rect = QRectF(pet.x - 40, pet.y - 40, 80, 80)
        fire_rect = QRectF(self.pos.x() - 20, self.pos.y() - 20, 40, 40)
        if pet_rect.intersects(fire_rect):
            self.impacting = True
            self.frame_idx = 0
            self.timer = 0
            return True
        return False

    def current_frame(self):
        if self.impacting:
            if self.impact_frames and self.frame_idx < len(self.impact_frames):
                return self.impact_frames[self.frame_idx]
        else:
            if self.frames:
                return self.frames[self.frame_idx % len(self.frames)]
        return None

# -------------------- 格林之子 --------------------
class Pet:
    NON_LOOP_STATES = {'turn_to_idle', 'tele_out', 'tele_in', 'sleep_anim',
                       'wake', 'antic', 'shoot', 'burst'}

    def __init__(self, stage=1):
        self.stage = stage
        self.state = 'tele_in'
        self.x = random.randint(200, 800)
        self.y = random.randint(200, 500)
        self.vx = random.choice([-1.5, 1.5])
        self.vy = random.choice([-0.8, 0.8])
        self.direction = 1  # 1 = 向右
        self.pending_direction = None

        self.anim_frames = []
        self.anim_idx = 0
        self.anim_timer = 0
        self.anim_loop = True
        self.anim_finished = False

        self.max_hp = self.stage
        self.hp = self.max_hp

        self.state_timer = 0
        self.growth_timer = random.randint(60*60, 300*60)  # 1~5分钟（60fps）
        self.sleep_cooldown = random.randint(600, 1800)    # 10~30秒
        self.sleep_duration = 0
        self.attack_cooldown = 0
        self.attack_target = None
        self.pre_attack_state = 'fly'

        self.teleport_timer = random.randint(600, 1800)    # 10~30秒
        self.pending_removal = False
        self.owner = None
        self.hovering = False

        # 攻击移动模式
        self.attack_mode = None  # None, 'fly_move', 'post_teleport'
        self.attack_move_distance = 0
        self.attack_move_required = 120.0
        self.post_teleport_timer = 0
        self.no_target_attack = False

        # 飞行循环音效播放器
        self.fly_loop_player = None
        # 正常移动音效冷却（降低频率，约5秒播一次）
        self.idle_sound_cooldown = 0

        # 瞬移目标坐标
        self._teleport_target_x = None
        self._teleport_target_y = None
        # 瞬移后休眠标记
        self._sleep_after_teleport = None
        # 飞行到底部标记
        self.sleep_pending = None
        # 休眠目标 Y 坐标
        self.target_sleep_y = None

        self._update_anim()

    def _update_anim(self):
        anim_map = {
            'fly': ('fly', self.stage),
            'idle': ('idle', self.stage),
            'turn_to_idle': ('turntoidle', self.stage),
            'tele_out': ('tele_out', self.stage),
            'tele_in': ('tele_in', self.stage),
            'sleep_anim': ('sleep', self.stage),
            'sleep_still': ('sleep', self.stage),
            'wake': ('wake', self.stage),
            'antic': ('antic', self.stage),
            'shoot': ('shoot', self.stage),
            'burst': ('burst', None),
        }
        key = anim_map.get(self.state)
        if key is None:
            return
        frames = ANIM_FRAMES.get(key)
        if frames is None and key[1] is not None:
            # 当前阶段动画缺失，按顺序尝试其他阶段（1→4）
            for s in range(1, 5):
                frames = ANIM_FRAMES.get((key[0], s))
                if frames is not None:
                    break
        if frames:
            self.anim_frames = frames
            self.anim_idx = 0
            self.anim_timer = 0
            self.anim_finished = False
            self.anim_loop = self.state not in Pet.NON_LOOP_STATES
            if self.state == 'sleep_still':
                self.anim_loop = False
                if self.anim_frames:
                    self.anim_idx = len(self.anim_frames) - 1

    def _stop_fly_loop(self):
        """停止飞行循环音效"""
        if self.fly_loop_player is not None:
            self.fly_loop_player.stop()
            self.fly_loop_player.deleteLater()
            self.fly_loop_player = None

    def _start_fly_loop(self):
        """启动飞行循环音效"""
        global audio_manager
        if audio_manager is None:
            return
        if self.fly_loop_player is None:
            self.fly_loop_player = audio_manager.create_loop_player('fly_loop')
        if self.fly_loop_player is not None and audio_manager.audio_enabled:
            self.fly_loop_player.play()

    def _update_idle_sound(self):
        """每帧调用，定期播放正常移动音效（30~60秒一次）"""
        global audio_manager
        if audio_manager is None or self.attack_mode is not None:
            return
        self.idle_sound_cooldown -= 1
        if self.idle_sound_cooldown <= 0:
            if self.stage <= 3:
                audio_manager.play_sound('idle_1_3')
            else:
                audio_manager.play_sound('idle_4')
            self.idle_sound_cooldown = random.randint(1800, 3600)  # 30~60秒

    def _trigger_state_sound(self):
        """根据状态变化播放对应音效"""
        global audio_manager
        if audio_manager is None:
            return

        # 休眠状态不发出任何音效，停止正常移动音效
        if self.state in ('sleep_anim', 'sleep_still'):
            self._stop_fly_loop()
            return

        # 战斗状态（antic/shoot）：停止正常移动音效
        if self.state in ('antic', 'shoot'):
            self._stop_fly_loop()

        # 瞬移音效
        if self.state == 'tele_out':
            self._stop_fly_loop()
            audio_manager.play_sound('teleport_out')

        # 攻击音效（antic）
        elif self.state == 'antic':
            if self.stage <= 3:
                audio_manager.play_sound('attack_yelp_1_3')
            else:
                audio_manager.play_sound('attack_yelp_4')

        # 飞行移动音效（仅非战斗移动时启动飞行循环）
        if self.state == 'fly' and self.attack_mode is None:
            self._start_fly_loop()

    def change_state(self, new_state):
        if self.state == new_state:
            return
        self.state = new_state
        self.state_timer = 0
        self._update_anim()
        self._trigger_state_sound()

    def _target_alive(self):
        """检查攻击目标是否仍存活且存在于宠物列表中"""
        if self.attack_target is None or self.owner is None:
            return False
        return self.attack_target in self.owner.pets and not self.attack_target.pending_removal

    def _start_attack(self, target):
        """发起攻击，根据概率选择原地/飞行/瞬移"""
        if target is None or target == self:
            return
        # 面向目标
        dx = target.x - self.x
        self.pending_direction = 1 if dx >= 0 else -1
        self.attack_target = target
        self.pre_attack_state = self.state if self.state in ('fly', 'idle') else 'fly'
        self.vx = self.vy = 0
        self.hovering = False

        r = random.random()
        if r < 0.5:
            # 原地攻击
            self.change_state('antic')
        elif r < 0.75:
            # 飞行移动一段距离后攻击
            self.attack_mode = 'fly_move'
            dx = target.x - self.x
            dy = target.y - self.y
            dist = math.hypot(dx, dy)
            if dist < 1: dist = 1
            self.vx = (dx / dist) * 3.0
            self.vy = (dy / dist) * 3.0
            self.state = 'fly'
            self._update_anim()
            self.attack_move_distance = 0
        else:
            # 瞬移到目标附近后移动0.1秒再攻击（播放完整瞬移动画）
            angle = random.uniform(0, 2 * math.pi)
            radius = 80 + random.uniform(0, 40)
            target_x = target.x + math.cos(angle) * radius
            target_y = target.y + math.sin(angle) * radius
            screen = QApplication.primaryScreen().geometry()
            target_x = max(80, min(screen.width() - 80, target_x))
            target_y = max(80, min(screen.height() - 80, target_y))
            self._teleport_target_x = target_x
            self._teleport_target_y = target_y
            # 设置向目标方向移动的速度
            dx = target.x - target_x
            dy = target.y - target_y
            dist = math.hypot(dx, dy)
            if dist < 1: dist = 1
            self.vx = (dx / dist) * 3.0
            self.vy = (dy / dist) * 3.0
            self.attack_mode = 'post_teleport'
            self.post_teleport_timer = 6  # 0.1秒 ≈ 6帧
            self.change_state('tele_out')

    def hit(self, damage, attacker=None):
        if self.hp <= 0:
            return
        self.hp -= damage
        # 设置朝向为攻击者方向
        if attacker is not None:
            dx = attacker.x - self.x
            self.pending_direction = 1 if dx >= 0 else -1
            # 如果在休眠，唤醒并反击
            if self.state in ('sleep_anim', 'sleep_still'):
                self.hovering = False
                self.change_state('wake')
                self._start_attack(attacker)
                return
        if self.hp <= 0:
            if attacker is not None and attacker.hp > 0:
                attacker.on_kill()
            self._die()
        else:
            # 非休眠状态下受伤，立即反击（中断当前动作）
            if attacker is not None:
                self._start_attack(attacker)

    def on_kill(self):
        if self.stage < 4:
            self.stage += 1
            self.max_hp = self.stage
        self.hp = self.max_hp
        # 击败后立即瞬移展示新形态
        self.attack_mode = None
        self.attack_target = None
        self.no_target_attack = False
        self._stop_fly_loop()
        self.change_state('tele_out')

    def _die(self):
        self._stop_fly_loop()
        if self.state != 'tele_out':
            self.change_state('tele_out')
            self.pending_removal = True

    def current_frame(self):
        if self.anim_frames and self.anim_idx < len(self.anim_frames):
            return self.anim_frames[self.anim_idx]
        return None

    def hit_test(self, pos):
        margin = 50
        return (self.x - margin < pos.x() < self.x + margin and
                self.y - margin < pos.y() < self.y + margin)

    def update(self):
        # 攻击移动处理
        if self.attack_mode == 'fly_move':
            old_x, old_y = self.x, self.y
            self.x += self.vx
            self.y += self.vy
            self.attack_move_distance += math.hypot(self.x - old_x, self.y - old_y)
            # 目标消失则取消攻击
            if not self._target_alive():
                self.attack_mode = None
                self.attack_target = None
                self.vx = random.choice([-1.5, 1.5])
                self.vy = random.choice([-0.8, 0.8])
                self.change_state('fly')
                return
            if self.attack_move_distance >= self.attack_move_required:
                self.attack_mode = None
                self.vx = self.vy = 0
                self.change_state('antic')
                return
            # 移动时仍更新动画
            if self.anim_frames:
                self.anim_timer += 1
                if self.anim_timer % 4 == 0:
                    self.anim_idx = (self.anim_idx + 1) % len(self.anim_frames)
            # 面向运动方向
            if self.vx != 0:
                self.direction = 1 if self.vx >= 0 else -1
            return

        # 瞬移后短暂移动处理（受攻击后瞬移，移动0.1秒后攻击）
        if self.attack_mode == 'post_teleport' and self.state == 'fly':
            self.post_teleport_timer -= 1
            self.x += self.vx
            self.y += self.vy
            if not self._target_alive():
                self.attack_mode = None
                self.attack_target = None
                self.vx = random.choice([-1.5, 1.5])
                self.vy = random.choice([-0.8, 0.8])
                self.change_state('fly')
                return
            if self.post_teleport_timer <= 0:
                self.attack_mode = None
                self.vx = self.vy = 0
                self.change_state('antic')
                return
            # 移动时更新动画
            if self.anim_frames:
                self.anim_timer += 1
                if self.anim_timer % 4 == 0:
                    self.anim_idx = (self.anim_idx + 1) % len(self.anim_frames)
            # 朝向
            if self.vx != 0:
                self.direction = 1 if self.vx >= 0 else -1
            return

        # 悬停处理
        if self.hovering:
            self.vx = self.vy = 0
            if self.state not in ('idle', 'turn_to_idle', 'sleep_anim', 'sleep_still'):
                self.change_state('idle')
        else:
            self.state_timer += 1
            self._update_timers()

            # 持续攻击：冷却结束后自动重新攻击目标
            if self.attack_target is not None and self.attack_cooldown <= 0 and self.state in ('fly', 'idle'):
                if self._target_alive():
                    self._start_attack(self.attack_target)

            if self.state == 'fly':
                self._move_random()
                self._update_idle_sound()
                if self._is_stationary():
                    self.change_state('turn_to_idle')
            elif self.state == 'idle':
                if not self._is_stationary():
                    self.change_state('fly')
            elif self.state == 'turn_to_idle':
                if self.anim_finished:
                    self.change_state('idle')
            elif self.state == 'tele_out':
                if self.anim_finished:
                    if self._teleport_target_x is not None:
                        self.x = self._teleport_target_x
                        self.y = self._teleport_target_y
                        self._teleport_target_x = None
                        self._teleport_target_y = None
                    else:
                        screen = QApplication.primaryScreen().geometry()
                        self.x = random.randint(150, screen.width() - 150)
                        self.y = random.randint(150, screen.height() - 150)
                    self.change_state('tele_in')
            elif self.state == 'tele_in':
                if self.anim_finished:
                    if self._sleep_after_teleport:
                        self._sleep_after_teleport = None
                        self.change_state('sleep_anim')
                    elif self.attack_mode == 'post_teleport':
                        # 攻击瞬移完成后进入移动阶段，朝向目标方向
                        self.state = 'fly'
                        self._update_anim()
                    else:
                        self.vx = random.choice([-1.5, 1.5])
                        self.vy = random.choice([-0.8, 0.8])
                        self.change_state('fly')
            elif self.state == 'sleep_anim':
                if self.anim_finished:
                    self.change_state('sleep_still')
                    self.sleep_duration = random.randint(600, 3600)
            elif self.state == 'sleep_still':
                if not self.hovering:
                    self.sleep_duration -= 1
                    if self.sleep_duration <= 0:
                        self.change_state('wake')
            elif self.state == 'wake':
                if self.anim_finished:
                    if random.random() < 0.5:
                        self.change_state('tele_out')
                    else:
                        self.vx = random.choice([-1.5, 1.5])
                        self.vy = random.choice([-0.8, 0.8])
                        self.change_state('fly')
                    self.sleep_cooldown = random.randint(600, 1800)
            elif self.state == 'antic':
                # 无目标攻击（菜单攻击键，无其他宠物时）
                if self.no_target_attack:
                    if self.anim_finished:
                        self.change_state('shoot')
                elif not self._target_alive():
                    self.attack_target = None
                    self.vx = random.choice([-1.5, 1.5])
                    self.vy = random.choice([-0.8, 0.8])
                    self.change_state('fly')
                elif self.anim_finished:
                    self.change_state('shoot')
            elif self.state == 'shoot':
                if self.anim_finished:
                    if self.no_target_attack:
                        dx = 200 * self.direction
                        fb = Fireball(QPointF(self.x, self.y),
                                      QPointF(self.x + dx, self.y),
                                      owner=self)
                        if self.owner:
                            self.owner.fireballs.append(fb)
                        self.no_target_attack = False
                        self.attack_target = None
                        self.vx = random.choice([-1.5, 1.5])
                        self.vy = random.choice([-0.8, 0.8])
                        self.change_state(self.pre_attack_state)
                    elif self._target_alive():
                        target = self.attack_target
                        fb = Fireball(QPointF(self.x, self.y),
                                      QPointF(target.x, target.y),
                                      owner=self)
                        if self.owner:
                            self.owner.fireballs.append(fb)
                        # 冷却2秒后继续攻击，直到目标死亡
                        self.attack_cooldown = 120
                        self.attack_target = target
                        self.vx = random.choice([-1.5, 1.5])
                        self.vy = random.choice([-0.8, 0.8])
                        self.change_state(self.pre_attack_state)
                    else:
                        # 目标已死亡，恢复正常移动
                        self.attack_target = None
                        self.vx = random.choice([-1.5, 1.5])
                        self.vy = random.choice([-0.8, 0.8])
                        self.change_state(self.pre_attack_state)
            elif self.state == 'burst':
                if self.anim_finished:
                    if self.stage < 4:
                        self.stage += 1
                        self.max_hp = self.stage
                        self.hp = self.max_hp
                    self.growth_timer = random.randint(3600, 18000)
                    self.vx = random.choice([-1.5, 1.5])
                    self.vy = random.choice([-0.8, 0.8])
                    self.change_state('fly')

        # 动画更新
        if self.anim_frames:
            self.anim_timer += 1
            delay = 4
            if self.state in ('tele_out', 'tele_in'):
                delay = 3
            if self.anim_timer >= delay:
                self.anim_timer = 0
                if self.anim_loop:
                    self.anim_idx = (self.anim_idx + 1) % len(self.anim_frames)
                else:
                    if self.anim_idx < len(self.anim_frames) - 1:
                        self.anim_idx += 1
                    else:
                        self.anim_finished = True

        # 朝向
        if self.pending_direction is not None:
            self.direction = self.pending_direction
            self.pending_direction = None
        elif self.state == 'fly' and not self.hovering:
            if self.vx != 0:
                self.direction = 1 if self.vx >= 0 else -1

    def _is_stationary(self):
        return abs(self.vx) < 0.1 and abs(self.vy) < 0.1

    def _move_random(self):
        if random.random() < 0.02:
            self.vx += random.uniform(-0.3, 0.3)
            self.vy += random.uniform(-0.3, 0.3)
            sp = math.hypot(self.vx, self.vy)
            if sp > 3.0:
                self.vx = self.vx / sp * 3.0
                self.vy = self.vy / sp * 3.0
            elif sp < 1.0:
                self.vx = self.vx / (sp + 0.1) * 1.5
                self.vy = self.vy / (sp + 0.1) * 1.5
        self.x += self.vx
        self.y += self.vy
        screen = QApplication.primaryScreen().geometry()
        margin = 80
        if self.x < margin:
            self.x = margin
            self.vx *= -1
        elif self.x > screen.width() - margin:
            self.x = screen.width() - margin
            self.vx *= -1
        if self.y < margin:
            self.y = margin
            self.vy *= -1
        elif self.y > screen.height() - margin:
            self.y = screen.height() - margin
            self.vy *= -1

    def _update_timers(self):
        if self.state in ('fly', 'idle', 'turn_to_idle'):
            self.growth_timer -= 1
            if self.growth_timer <= 0 and self.stage < 4:
                self.vx = self.vy = 0
                self.change_state('burst')
                return
            self.teleport_timer -= 1
            if self.teleport_timer <= 0:
                self.vx = self.vy = 0
                self.change_state('tele_out')
                self.teleport_timer = random.randint(600, 1800)
                return
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.state in ('fly', 'idle') and not self.hovering:
            self.sleep_cooldown -= 1
            if self.sleep_cooldown <= 0:
                self.initiate_sleep()

    def initiate_sleep(self):
        self.vx = self.vy = 0
        self._stop_fly_loop()
        screen = QApplication.primaryScreen().geometry()
        if random.random() < 0.5:
            self.target_sleep_y = screen.height() - 100
            self.vy = 1.5
            self.state = 'fly'
            self._update_anim()
            self.sleep_pending = 'fly_to_bottom'
        else:
            # 瞬移到屏幕底部休眠位置，走完整瞬移动画
            target_x = max(100, min(screen.width() - 100, self.x))
            target_y = screen.height() - 100
            self._teleport_target_x = target_x
            self._teleport_target_y = target_y
            self._sleep_after_teleport = True
            self.change_state('tele_out')
        self.sleep_cooldown = random.randint(600, 1800)

# -------------------- 桌面窗口 --------------------
class DeskPetWindow(QWidget):
    FLIP_X = QTransform().scale(-1, 1)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.pets = []
        self.fireballs = []

        self.dragging_pet = None
        self.drag_offset = QPointF(0, 0)

        # 右键后左键触发移动状态
        self.right_clicked_pet = None

        # 自动生成计时器：每10分钟（37500帧 @ 16ms/帧）生成一次
        self.split_timer = 37500
        # 自动攻击计时器：每3分钟（11250帧 @ 16ms/帧）攻击一次
        self.auto_attack_timer = 11250

        first_pet = Pet(stage=1)
        first_pet.owner = self
        self.pets.append(first_pet)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)

        self.init_tray()

    def init_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon.fromTheme("face-smile"))
        tray_menu = QMenu()
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        self.tray.setContextMenu(tray_menu)
        self.tray.show()

    def game_loop(self):
        # 飞行到底部检测
        for pet in self.pets:
            if pet.sleep_pending == 'fly_to_bottom':
                if pet.y >= pet.target_sleep_y:
                    pet.y = pet.target_sleep_y
                    pet.vy = 0
                    pet.change_state('sleep_anim')
                    pet.sleep_pending = None

        # 清理死亡宠物前，解除其他宠物的攻击目标，并停止死亡宠物的音效
        for pet in self.pets:
            if pet.pending_removal:
                pet._stop_fly_loop()
                for other in self.pets:
                    if other.attack_target is pet:
                        other.attack_target = None
                        if other.state in ('antic', 'shoot'):
                            other.vx = random.choice([-1.5, 1.5])
                            other.vy = random.choice([-0.8, 0.8])
                            other.change_state('fly')

        # 更新宠物
        for pet in self.pets[:]:
            pet.update()
            if pet.pending_removal and pet.state == 'tele_out' and pet.anim_finished:
                pet._stop_fly_loop()
                self.pets.remove(pet)

        # 火球更新与碰撞
        for fb in self.fireballs[:]:
            fb.update()
            if not fb.active:
                self.fireballs.remove(fb)
                continue
            for pet in self.pets:
                if fb.hit_check(pet):
                    pet.hit(1, attacker=fb.owner)
                    break

        self.handle_split()
        self.handle_random_attack()
        self.update()

    def handle_split(self):
        if len(self.pets) >= 4:
            return
        self.split_timer -= 1
        if self.split_timer <= 0:
            self.split_timer = 37500  # 重置为10分钟
            used_stages = {p.stage for p in self.pets}
            missing = [s for s in range(1,5) if s not in used_stages]
            if not missing:
                return
            source = random.choice(self.pets)
            new_stage = random.choice(missing)
            new_pet = Pet(stage=new_stage)
            new_pet.owner = self
            new_pet.x = source.x + random.randint(-60, 60)
            new_pet.y = source.y + random.randint(-60, 60)
            new_pet.state = 'tele_in'
            new_pet._update_anim()
            self.pets.append(new_pet)
            source.attack_cooldown = max(source.attack_cooldown, 120)

    def handle_random_attack(self):
        if len(self.pets) < 2:
            return
        self.auto_attack_timer -= 1
        if self.auto_attack_timer <= 0:
            self.auto_attack_timer = 11250  # 重置为3分钟
            candidates = [p for p in self.pets if p.state in ('fly', 'idle') and p.attack_cooldown <= 0 and not p.hovering]
            if not candidates:
                return
            attacker = random.choice(candidates)
            targets = [p for p in self.pets if p != attacker]
            if not targets:
                return
            target = random.choice(targets)
            attacker._start_attack(target)
            attacker.attack_cooldown = 180

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            clicked_pet = None
            for pet in self.pets:
                if pet.hit_test(event.pos()):
                    clicked_pet = pet
                    break
            if clicked_pet:
                self.right_clicked_pet = clicked_pet
                clicked_pet.hovering = True
                clicked_pet.vx = clicked_pet.vy = 0
                if clicked_pet.state not in ('idle', 'sleep_anim', 'sleep_still'):
                    clicked_pet.change_state('idle')
                self.show_context_menu(clicked_pet, event.globalPos())
                clicked_pet.hovering = False
                if clicked_pet.state == 'idle':
                    clicked_pet.vx = random.choice([-1.5, 1.5])
                    clicked_pet.vy = random.choice([-0.8, 0.8])
                    clicked_pet.change_state('fly')
            else:
                self.lower()
        elif event.button() == Qt.LeftButton:
            # 右键后左键任意区域 → 格林之子切换为移动状态
            if self.right_clicked_pet is not None:
                rp = self.right_clicked_pet
                self.right_clicked_pet = None
                if rp in self.pets and not rp.pending_removal:
                    rp.hovering = False
                    if rp.state == 'idle':
                        rp.change_state('fly')
                    rp.vx = random.choice([-1.5, 1.5])
                    rp.vy = random.choice([-0.8, 0.8])
            # 继续处理左键拖拽
            click_pos = event.pos()
            for pet in self.pets:
                if pet.hit_test(click_pos):
                    self.dragging_pet = pet
                    self.drag_offset = QPointF(pet.x - click_pos.x(), pet.y - click_pos.y())
                    pet.hovering = True
                    pet.vx = pet.vy = 0
                    break
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging_pet is not None:
            new_pos = event.pos()
            self.dragging_pet.x = new_pos.x() + self.drag_offset.x()
            self.dragging_pet.y = new_pos.y() + self.drag_offset.y()
            screen = QApplication.primaryScreen().geometry()
            margin = 80
            self.dragging_pet.x = max(margin, min(screen.width() - margin, self.dragging_pet.x))
            self.dragging_pet.y = max(margin, min(screen.height() - margin, self.dragging_pet.y))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging_pet is not None:
            pet = self.dragging_pet
            pet.hovering = False
            pet.change_state('fly')
            pet.vx = random.choice([-1.5, 1.5])
            pet.vy = random.choice([-0.8, 0.8])
            self.dragging_pet = None

    def show_context_menu(self, pet, pos):
        menu = QMenu(self)

        retain_action = menu.addAction("保留一个")
        retain_action.triggered.connect(lambda: self.retain_one(pet))

        stage_menu = menu.addMenu("生长阶段")
        stage_group = QActionGroup(stage_menu)
        for i in range(1,5):
            action = QAction(f"阶段 {i}", stage_menu, checkable=True)
            if i == pet.stage:
                action.setChecked(True)
            action.triggered.connect(lambda checked, s=i: self.set_pet_stage(pet, s))
            stage_group.addAction(action)
            stage_menu.addAction(action)

        sleep_action = menu.addAction("休眠")
        sleep_action.triggered.connect(lambda: self.sleep_pet(pet))

        wake_action = menu.addAction("唤醒")
        wake_action.triggered.connect(lambda: self.wake_pet(pet))

        split_action = menu.addAction("分裂")
        split_action.triggered.connect(lambda: self.split_pet(pet))

        tele_action = menu.addAction("瞬移")
        tele_action.triggered.connect(lambda: self.teleport_pet(pet))

        attack_action = menu.addAction("攻击")
        attack_action.triggered.connect(lambda: self.attack_from_menu(pet))

        if len(self.pets) >= 2:
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(lambda: self.delete_pet(pet))

        menu.addSeparator()

        # 背景音乐子菜单
        global audio_manager
        bgm_menu = menu.addMenu("背景音乐")
        bgm_group = QActionGroup(bgm_menu)
        bgm_grimm_action = QAction("Grimm", bgm_menu, checkable=True)
        bgm_epic_action = QAction("Grimm Epic Layer", bgm_menu, checkable=True)

        if audio_manager is not None and audio_manager.current_bgm == 'bgm_grimm':
            bgm_grimm_action.setChecked(True)
        elif audio_manager is not None and audio_manager.current_bgm == 'bgm_epic':
            bgm_epic_action.setChecked(True)

        bgm_grimm_action.triggered.connect(lambda: self.set_bgm('bgm_grimm'))
        bgm_epic_action.triggered.connect(lambda: self.set_bgm('bgm_epic'))
        bgm_group.addAction(bgm_grimm_action)
        bgm_group.addAction(bgm_epic_action)
        bgm_menu.addAction(bgm_grimm_action)
        bgm_menu.addAction(bgm_epic_action)

        bgm_menu.addSeparator()

        # 音量调节（手动输入）
        vol_action = bgm_menu.addAction("音量调节")
        vol_action.triggered.connect(self.manual_set_bgm_volume)

        # 关闭背景音乐
        close_bgm_action = bgm_menu.addAction("关闭")
        close_bgm_action.triggered.connect(self.stop_bgm)

        # 停止/开始音频
        if audio_manager is not None and audio_manager.audio_enabled:
            audio_toggle_action = menu.addAction("停止音频")
        else:
            audio_toggle_action = menu.addAction("开始音频")
        audio_toggle_action.triggered.connect(self.toggle_audio)

        menu.addSeparator()
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(QApplication.quit)

        menu.exec_(pos)

    def retain_one(self, pet):
        for p in self.pets[:]:
            if p is not pet:
                p._die()
                p.pending_removal = True

    def set_pet_stage(self, pet, stage):
        if pet.stage != stage:
            pet.stage = stage
            pet.max_hp = stage
            pet.hp = stage
            pet._update_anim()
            pet.growth_timer = random.randint(3600, 18000)

    def wake_pet(self, pet):
        if pet.state in ('sleep_anim', 'sleep_still'):
            pet.hovering = False
            pet.sleep_duration = 0
            if random.random() < 0.5:
                pet.change_state('tele_out')
            else:
                pet.change_state('wake')
            pet.sleep_cooldown = random.randint(600, 1800)

    def sleep_pet(self, pet):
        pet.hovering = False
        pet.initiate_sleep()

    def split_pet(self, pet):
        if len(self.pets) >= 4:
            return
        used_stages = {p.stage for p in self.pets}
        missing = [s for s in range(1,5) if s not in used_stages]
        if not missing:
            return
        new_stage = random.choice(missing)
        new_pet = Pet(stage=new_stage)
        new_pet.owner = self
        new_pet.x = pet.x + random.randint(-60, 60)
        new_pet.y = pet.y + random.randint(-60, 60)
        new_pet.state = 'tele_in'
        new_pet._update_anim()
        self.pets.append(new_pet)
        pet.attack_cooldown = max(pet.attack_cooldown, 120)

    def teleport_pet(self, pet):
        pet.hovering = False
        pet.change_state('tele_out')

    def attack_from_menu(self, pet):
        targets = [p for p in self.pets if p != pet]
        if targets:
            target = random.choice(targets)
            pet._start_attack(target)
        else:
            # 无目标，播放攻击动画后向面向方向发射
            pet.no_target_attack = True
            pet.pre_attack_state = pet.state if pet.state in ('fly', 'idle') else 'fly'
            pet.vx = pet.vy = 0
            pet.hovering = False
            pet.change_state('antic')

    def delete_pet(self, pet):
        pet._die()
        pet.pending_removal = True

    def set_bgm(self, bgm_key):
        """设置背景音乐"""
        global audio_manager
        if audio_manager is not None:
            audio_manager.play_bgm(bgm_key)

    def set_bgm_volume(self, volume):
        """设置背景音乐音量"""
        global audio_manager
        if audio_manager is not None:
            audio_manager.set_bgm_volume(volume)

    def manual_set_bgm_volume(self):
        """手动输入背景音乐音量"""
        global audio_manager
        if audio_manager is None:
            return
        current = audio_manager.bgm_volume
        value, ok = QInputDialog.getInt(
            self, "音量调节", f"请输入音量 (0-100，当前: {current}):",
            value=current, min=0, max=100, step=5)
        if ok:
            self.set_bgm_volume(value)

    def stop_bgm(self):
        """关闭背景音乐"""
        global audio_manager
        if audio_manager is not None:
            audio_manager.stop_bgm()

    def toggle_audio(self):
        """切换音频开关"""
        global audio_manager
        if audio_manager is not None:
            audio_manager.toggle_audio()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for fb in self.fireballs:
            frame = fb.current_frame()
            if frame:
                painter.drawPixmap(int(fb.pos.x() - frame.width()//2),
                                   int(fb.pos.y() - frame.height()//2), frame)

        for pet in self.pets:
            frame = pet.current_frame()
            if frame:
                if pet.direction == -1:
                    frame = frame.transformed(DeskPetWindow.FLIP_X)
                painter.drawPixmap(int(pet.x - frame.width()//2),
                                   int(pet.y - frame.height()//2), frame)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Grimmchild Anim')
    try:
        load_animations(base_dir)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    # 初始化音频管理器
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'AudioClip')
    audio_manager = AudioManager(audio_dir)

    window = DeskPetWindow()
    window.show()
    sys.exit(app.exec_())