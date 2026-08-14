import sys, os, random, math
from PyQt5.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu,
                             QAction, QActionGroup, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QUrl
from PyQt5.QtGui import QPixmap, QPainter, QTransform, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

def get_int_input(title, label, value, min_val, max_val, step=1):
    dialog = QInputDialog()
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    dialog.setInputMode(QInputDialog.IntInput)
    dialog.setWindowTitle(title); dialog.setLabelText(label)
    dialog.setIntValue(value); dialog.setIntMinimum(min_val)
    dialog.setIntMaximum(max_val); dialog.setIntStep(step)
    return (dialog.intValue(), True) if dialog.exec_() == QInputDialog.Accepted else (0, False)

ANIM_FRAMES = {}
audio_manager = None

def load_animations(base_dir):
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"目录不存在: {base_dir}")
    name_mapping = {
        'flameball impact': 'flameball_impact', 'flameball': 'flameball', 'burst': 'burst',
        'fly': 'fly', 'turntoidle': 'turntoidle', 'tele out': 'tele_out', 'tele in': 'tele_in',
        'wake': 'wake', 'sleep': 'sleep', 'shoot': 'shoot', 'antic': 'antic', 'idle': 'idle',
    }
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path): continue
        parts = folder.split('.', 1)
        if len(parts) < 2: continue
        raw_name = parts[1].strip().lower()
        anim_base = stage = None
        for key in name_mapping:
            if raw_name.startswith(key):
                anim_base = name_mapping[key]
                rest = raw_name[len(key):].strip()
                if rest.isdigit(): stage = int(rest)
                break
        if anim_base is None: continue
        frames = [(int(f.split('-')[1]), os.path.join(folder_path, f))
                  for f in sorted(os.listdir(folder_path))
                  if f.lower().endswith('.png') and '-' in f and f.split('-')[1].isdigit()]
        frames.sort(key=lambda x: x[0])
        pixmaps = [QPixmap(path) for _, path in frames]
        if pixmaps: ANIM_FRAMES[(anim_base, stage)] = pixmaps

class AudioManager:
    def __init__(self, audio_dir):
        self.audio_dir = audio_dir; self.audio_enabled = True
        self.bgm_player = None; self.current_bgm = None; self.bgm_volume = 100
        self._players = []
        sounds_map = {
            'attack_yelp_1_3': '1Grimmbat_attack_yelp_1~3.mp3',
            'attack_yelp_4': '1Grimmbat_attack_yelp_4.mp3',
            'fireball_yelp_1_3': '2Grimmbat_attack_yelp_1~3.mp3',
            'fireball_yelp_4': '2Grimmbat_attack_yelp_4.mp3',
            'teleport_out': 'grimm_teleport_out.mp3',
            'idle_1_3': 'Grimmbat_idle_1~3.mp3', 'idle_4': 'Grimmbat_idle_4.mp3',
            'fly_loop': 'grimmchild_fly_loop.mp3', 'fireball_shoot': 'grimmchild_fireball_shoot.mp3',
            'bgm_grimm': 'Grimm.mp3', 'bgm_epic': 'Grimm Epic Layer.mp3',
        }
        self.sounds = {k: os.path.join(audio_dir, v) for k, v in sounds_map.items()
                       if os.path.exists(os.path.join(audio_dir, v))}

    def _make_player(self, key):
        if key not in self.sounds: return None
        player = QMediaPlayer()
        player.setMedia(QMediaContent(QUrl.fromLocalFile(self.sounds[key])))
        return player

    def _cleanup(self, player, status):
        if status == QMediaPlayer.EndOfMedia and player in self._players:
            self._players.remove(player); player.deleteLater()

    def play_sound(self, key):
        if not self.audio_enabled or key not in self.sounds: return
        player = self._make_player(key)
        player.mediaStatusChanged.connect(lambda s, p=player: self._cleanup(p, s))
        player.play(); self._players.append(player)

    def create_loop_player(self, key):
        player = self._make_player(key)
        if player:
            player.mediaStatusChanged.connect(
                lambda s, p=player: (p.setPosition(0), p.play()) if s == QMediaPlayer.EndOfMedia else None)
        return player

    def play_bgm(self, key):
        if self.bgm_player: self.bgm_player.stop(); self.bgm_player.deleteLater()
        if key in self.sounds:
            self.bgm_player = self._make_player(key)
            self.bgm_player.setVolume(self.bgm_volume)
            self.bgm_player.mediaStatusChanged.connect(
                lambda s: (self.bgm_player.setPosition(0), self.bgm_player.play())
                if s == QMediaPlayer.EndOfMedia else None)
            if self.audio_enabled: self.bgm_player.play()
            self.current_bgm = key

    def stop_bgm(self):
        if self.bgm_player:
            self.bgm_player.stop(); self.bgm_player.deleteLater()
            self.bgm_player = None; self.current_bgm = None

    def set_bgm_volume(self, vol):
        self.bgm_volume = vol
        if self.bgm_player: self.bgm_player.setVolume(vol)

    def stop_all(self):
        for p in self._players[:]:
            try: p.stop()
            except: pass
        self._players.clear()
        if self.bgm_player: self.bgm_player.stop()

    def toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        if not self.audio_enabled: self.stop_all()
        elif self.bgm_player and self.current_bgm: self.bgm_player.play()
        return self.audio_enabled

class Fireball:
    def __init__(self, start_pos, target_pos, owner=None, speed=12):
        self.pos = QPointF(start_pos); self.target_pos = QPointF(target_pos); self.owner = owner
        dx, dy = target_pos.x() - start_pos.x(), target_pos.y() - start_pos.y()
        dist = math.hypot(dx, dy) or 1
        self.vx, self.vy = dx / dist * speed, dy / dist * speed
        self.active = True; self.impacting = False
        self.frames = ANIM_FRAMES.get(('flameball', None), [])
        self.impact_frames = ANIM_FRAMES.get(('flameball_impact', None), [])
        self.frame_idx = 0; self.timer = 0
        self.screen_rect = QApplication.primaryScreen().geometry()
        if audio_manager and owner:
            audio_manager.play_sound('fireball_yelp_1_3' if owner.stage <= 3 else 'fireball_yelp_4')
            audio_manager.play_sound('fireball_shoot')

    def update(self):
        if self.impacting:
            self.timer += 1
            if self.timer % 3 == 0:
                self.frame_idx += 1
                if self.frame_idx >= len(self.impact_frames): self.active = False
            return
        self.pos += QPointF(self.vx, self.vy)
        self.timer += 1
        if self.frames and self.timer % 3 == 0: self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        if (self.pos.x() < -100 or self.pos.x() > self.screen_rect.width() + 100 or
            self.pos.y() < -100 or self.pos.y() > self.screen_rect.height() + 100):
            self.active = False

    def hit_check(self, pet):
        if not self.active or self.impacting or pet is self.owner: return False
        if QRectF(pet.x - 40, pet.y - 40, 80, 80).intersects(
            QRectF(self.pos.x() - 20, self.pos.y() - 20, 40, 40)):
            self.impacting = True; self.frame_idx = 0; self.timer = 0; return True
        return False

    def current_frame(self):
        if self.impacting and self.impact_frames and self.frame_idx < len(self.impact_frames):
            return self.impact_frames[self.frame_idx]
        if not self.impacting and self.frames: return self.frames[self.frame_idx % len(self.frames)]
        return None

class Pet:
    FLY, IDLE, TURN_TO_IDLE, TELE_OUT, TELE_IN, SLEEP_ANIM, SLEEP_STILL, WAKE, ANTIC, SHOOT, BURST = (
        'fly', 'idle', 'turn_to_idle', 'tele_out', 'tele_in',
        'sleep_anim', 'sleep_still', 'wake', 'antic', 'shoot', 'burst'
    )
    NON_LOOP_STATES = {TURN_TO_IDLE, TELE_OUT, TELE_IN, SLEEP_ANIM, WAKE, ANTIC, SHOOT, BURST}

    def __init__(self, stage=1):
        self.stage = stage; self.state = self.TELE_IN
        self.x = random.randint(200, 800); self.y = random.randint(200, 500)
        self._random_motion()
        self.direction = 1; self.pending_direction = None
        self.anim_frames = []; self.anim_idx = 0; self.anim_timer = 0
        self.anim_loop = True; self.anim_finished = False
        self.max_hp = stage; self.hp = self.max_hp
        self.growth_timer = random.randint(3750, 11250)
        self.sleep_cooldown = random.randint(600, 1800)
        self.sleep_duration = 0; self.attack_cooldown = 0
        self.attack_target = None; self.pre_attack_state = self.FLY
        self.teleport_timer = random.randint(600, 1800)
        self.pending_removal = False; self.owner = None; self.hovering = False
        self.attack_mode = None; self.attack_move_distance = 0
        self.attack_move_required = 120.0; self.post_teleport_timer = 0
        self.no_target_attack = False; self.battle_royale = False
        self._just_changed_state = False
        self.fly_loop_player = None; self.idle_sound_cooldown = 0
        self._teleport_target_x = None; self._teleport_target_y = None
        self._sleep_after_teleport = None; self.sleep_pending = None; self.target_sleep_y = None
        self._turn_pending = False; self._pending_turn_dir = None
        self._turn_speed_x = 0; self._turn_vy = 0
        self._update_anim()

    def _random_motion(self): self.vx = random.choice([-1.5, 1.5]); self.vy = random.choice([-0.8, 0.8])
    def can_attack(self): return self.stage >= 2

    def _apply_owner_hp(self):
        if self.owner and hasattr(self.owner, 'stage_hp'):
            self.max_hp = self.owner.stage_hp.get(self.stage, self.stage)
            self.hp = self.max_hp

    def _battle_targets(self):
        return [p for p in self.owner.pets if p is not self and not p.pending_removal] if self.owner else []

    def _battle_continue(self):
        """大乱斗模式下寻找下一个目标，找到返回True"""
        if self.owner and self.owner.peace_mode: return False
        if not self.battle_royale: return False
        targets = self._battle_targets()
        if targets: self.attack_cooldown = 0; self._start_attack(random.choice(targets)); return True
        self.battle_royale = False; return False

    def _update_anim(self):
        anim_map = {
            self.FLY: ('fly', self.stage), self.IDLE: ('idle', self.stage),
            self.TURN_TO_IDLE: ('turntoidle', self.stage), self.TELE_OUT: ('tele_out', self.stage),
            self.TELE_IN: ('tele_in', self.stage), self.SLEEP_ANIM: ('sleep', self.stage),
            self.SLEEP_STILL: ('sleep', self.stage), self.WAKE: ('wake', self.stage),
            self.ANTIC: ('antic', self.stage), self.SHOOT: ('shoot', self.stage), self.BURST: ('burst', None),
        }
        key = anim_map.get(self.state)
        if key is None: return
        frames = ANIM_FRAMES.get(key)
        if frames is None and key[1] is not None:
            frames = next((ANIM_FRAMES.get((key[0], s)) for s in range(1, 5) if ANIM_FRAMES.get((key[0], s))), None)
        if frames:
            self.anim_frames = frames; self.anim_idx = 0; self.anim_timer = 0; self.anim_finished = False
            self.anim_loop = self.state not in Pet.NON_LOOP_STATES
            if self.state is self.SLEEP_STILL:
                self.anim_loop = False
                if self.anim_frames: self.anim_idx = len(self.anim_frames) - 1

    def _stop_fly_loop(self):
        if self.fly_loop_player:
            self.fly_loop_player.stop(); self.fly_loop_player.deleteLater(); self.fly_loop_player = None

    def _start_fly_loop(self):
        if audio_manager is None: return
        if self.fly_loop_player is None: self.fly_loop_player = audio_manager.create_loop_player('fly_loop')
        if self.fly_loop_player and audio_manager.audio_enabled: self.fly_loop_player.play()

    def _update_idle_sound(self):
        if audio_manager is None or self.attack_mode is not None: return
        self.idle_sound_cooldown -= 1
        if self.idle_sound_cooldown <= 0:
            audio_manager.play_sound('idle_1_3' if self.stage <= 3 else 'idle_4')
            self.idle_sound_cooldown = random.randint(1800, 3600)

    def _trigger_state_sound(self):
        if audio_manager is None: return
        if self.state in (self.SLEEP_ANIM, self.SLEEP_STILL): self._stop_fly_loop(); return
        if self.state in (self.ANTIC, self.SHOOT): self._stop_fly_loop()
        if self.state is self.TELE_OUT: self._stop_fly_loop(); audio_manager.play_sound('teleport_out')
        elif self.state is self.ANTIC and self.can_attack():
            audio_manager.play_sound('attack_yelp_1_3' if self.stage <= 3 else 'attack_yelp_4')
        if self.state is self.FLY and self.attack_mode is None: self._start_fly_loop()

    def change_state(self, new_state):
        if new_state in (self.ANTIC, self.SHOOT) and not self.can_attack(): return
        if self.state == new_state: return
        self.state = new_state; self._update_anim(); self._trigger_state_sound()
        self._just_changed_state = True

    def _target_alive(self):
        return (self.attack_target and not self.attack_target.pending_removal
                and self.attack_target in self.owner.pets)

    def _on_target_lost(self):
        self.attack_mode = None; self.attack_target = None
        if self._battle_continue(): return
        self._random_motion(); self.change_state(self.FLY)

    def _start_attack(self, target):
        if not self.can_attack() or target is None or target is self: return
        self.pending_direction = 1 if target.x >= self.x else -1
        self.attack_target = target
        self.pre_attack_state = self.state if self.state in (self.FLY, self.IDLE) else self.FLY
        self.vx = self.vy = 0; self.hovering = False
        r = random.random()
        if r < 0.4:
            self.change_state(self.ANTIC)
        elif r < 0.5:
            self.attack_mode = 'fly_move'
            dx, dy = target.x - self.x, target.y - self.y
            dist = math.hypot(dx, dy) or 1
            self.vx, self.vy = dx / dist * 3.0, dy / dist * 3.0
            self.state = self.FLY; self._update_anim(); self.attack_move_distance = 0
        else:
            if r < 0.6:
                radius = 80 + random.uniform(0, 40); self.attack_mode = 'post_teleport'
            else:
                radius = 500 + random.uniform(0, 200); self.attack_mode = 'teleport_far'
            angle = random.uniform(0, 2 * math.pi)
            tx = target.x + math.cos(angle) * radius; ty = target.y + math.sin(angle) * radius
            rect = self.owner.screen_rect
            tx = max(80, min(rect.width() - 80, tx)); ty = max(80, min(rect.height() - 80, ty))
            self._teleport_target_x = tx; self._teleport_target_y = ty
            dx, dy = target.x - tx, target.y - ty
            dist = math.hypot(dx, dy) or 1
            self.vx, self.vy = dx / dist * 3.0, dy / dist * 3.0
            self.post_teleport_timer = 6
            self.change_state(self.TELE_OUT)

    def hit(self, damage, attacker=None):
        if self.owner and self.owner.peace_mode: return
        if self.hp <= 0: return
        self.hp -= damage
        if attacker: self.pending_direction = 1 if attacker.x >= self.x else -1
        if self.hp <= 0:
            if attacker and attacker.hp > 0 and attacker.can_attack(): attacker.on_kill()
            self._die(); return
        if attacker:
            if self.state in (self.SLEEP_ANIM, self.SLEEP_STILL):
                self.hovering = False; self.change_state(self.WAKE)
            if self.can_attack(): self.attack_target = attacker; self.attack_cooldown = 0

    def on_kill(self):
        if self.stage < 4: self.stage += 1
        self._apply_owner_hp(); self.attack_mode = None; self.attack_target = None
        self.no_target_attack = False; self._stop_fly_loop(); self.change_state(self.TELE_OUT)

    def _die(self):
        self._stop_fly_loop()
        if self.state is not self.TELE_OUT: self.change_state(self.TELE_OUT)
        self.pending_removal = True

    def current_frame(self):
        return self.anim_frames[self.anim_idx] if self.anim_frames and self.anim_idx < len(self.anim_frames) else None

    def hit_test(self, pos):
        return self.x - 50 < pos.x() < self.x + 50 and self.y - 50 < pos.y() < self.y + 50

    def _move_random(self):
        if random.random() < 0.02:
            self.vx += random.uniform(-0.3, 0.3); self.vy += random.uniform(-0.3, 0.3)
            sp = math.hypot(self.vx, self.vy)
            if sp > 3.0: self.vx, self.vy = self.vx / sp * 3.0, self.vy / sp * 3.0
            elif sp < 1.0: self.vx, self.vy = self.vx / (sp + 0.1) * 1.5, self.vy / (sp + 0.1) * 1.5
        self.x += self.vx; self.y += self.vy
        rect = self.owner.screen_rect; margin = 80
        if self.x < margin:
            self.x = margin
            if self.direction == -1 and self.vx < 0 and not self._turn_pending and self.state is not self.TURN_TO_IDLE:
                self._turn_pending = True; self._pending_turn_dir = 1
                self._turn_speed_x = abs(self.vx); self._turn_vy = self.vy
            else: self.direction = 1; self.vx = abs(self.vx)
        elif self.x > rect.width() - margin:
            self.x = rect.width() - margin
            if self.direction == 1 and self.vx > 0 and not self._turn_pending and self.state is not self.TURN_TO_IDLE:
                self._turn_pending = True; self._pending_turn_dir = -1
                self._turn_speed_x = abs(self.vx); self._turn_vy = self.vy
            else: self.direction = -1; self.vx = -abs(self.vx)
        if self.y < margin: self.y = margin; self.vy *= -1
        elif self.y > rect.height() - margin: self.y = rect.height() - margin; self.vy *= -1

    def update(self):
        # 全状态有效的成长计时
        if not self.pending_removal and self.state != self.BURST:
            self.growth_timer -= 1
            if self.growth_timer <= 0 and self.stage < 4:
                self.attack_mode = None; self.attack_target = None; self.no_target_attack = False
                self.vx = self.vy = 0; self.hovering = False; self._stop_fly_loop()
                self.change_state(self.BURST)
                self._advance_anim(3 if self.state in (self.TELE_OUT, self.TELE_IN) else 4)
                return

        # 攻击移动模式（fly_move / post_teleport / teleport_far 合并处理）
        if self.attack_mode in ('fly_move', 'post_teleport', 'teleport_far') and self.state is self.FLY:
            old_x, old_y = self.x, self.y
            self.x += self.vx; self.y += self.vy
            if self.attack_mode == 'fly_move':
                self.attack_move_distance += math.hypot(self.x - old_x, self.y - old_y)
                if self.attack_move_distance >= self.attack_move_required:
                    self.attack_mode = None; self.vx = self.vy = 0; self.change_state(self.ANTIC); return
            else:
                self.post_teleport_timer -= 1
                if self.post_teleport_timer <= 0:
                    self.attack_mode = None; self.vx = self.vy = 0; self.change_state(self.ANTIC); return
            if not self._target_alive(): return self._on_target_lost()
            self._advance_anim(4)
            if self.vx != 0: self.direction = 1 if self.vx >= 0 else -1
            return

        if self.hovering:
            self.vx = self.vy = 0
            if self.state not in (self.IDLE, self.TURN_TO_IDLE, self.SLEEP_ANIM, self.SLEEP_STILL):
                self.change_state(self.IDLE)
        else:
            self._update_timers()
            if (self.attack_target and self.attack_cooldown <= 0 and
                self.state in (self.FLY, self.IDLE) and self.can_attack()
                and not (self.owner and self.owner.peace_mode)):
                if self._target_alive(): self._start_attack(self.attack_target)

            if self.state is self.FLY:
                if self._turn_pending:
                    self._turn_pending = False; self.vx = self.vy = 0
                    self.change_state(self.TURN_TO_IDLE); return
                self._move_random(); self._update_idle_sound()
                if self._is_stationary(): self.change_state(self.TURN_TO_IDLE)
            elif self.state is self.IDLE:
                if not self._is_stationary(): self.change_state(self.FLY)
            elif self.state is self.TURN_TO_IDLE and self.anim_finished:
                if self._pending_turn_dir is not None:
                    self.direction = self._pending_turn_dir
                    self.vx = self._turn_speed_x * (1 if self.direction == 1 else -1)
                    self.vy = self._turn_vy
                    self.x = max(85, min(self.owner.screen_rect.width() - 85, self.x))
                    self._pending_turn_dir = None; self._turn_speed_x = 0; self._turn_vy = 0
                    self.change_state(self.FLY)
                else: self.change_state(self.IDLE)
            elif self.state is self.TELE_OUT and self.anim_finished:
                if self._teleport_target_x is not None:
                    self.x, self.y = self._teleport_target_x, self._teleport_target_y
                    self._teleport_target_x = self._teleport_target_y = None
                else:
                    rect = self.owner.screen_rect
                    self.x = random.randint(150, rect.width() - 150)
                    self.y = random.randint(150, rect.height() - 150)
                self.change_state(self.TELE_IN)
            elif self.state is self.TELE_IN and self.anim_finished:
                if self._sleep_after_teleport:
                    self._sleep_after_teleport = None; self.change_state(self.SLEEP_ANIM)
                elif self.attack_mode in ('post_teleport', 'teleport_far'):
                    self.state = self.FLY; self._update_anim()
                else:
                    self._random_motion(); self.change_state(self.FLY); self._battle_continue()
            elif self.state is self.SLEEP_ANIM and self.anim_finished:
                self.change_state(self.SLEEP_STILL); self.sleep_duration = random.randint(600, 3600)
            elif self.state is self.SLEEP_STILL and not self.hovering:
                self.sleep_duration -= 1
                if self.sleep_duration <= 0: self.change_state(self.WAKE)
            elif self.state is self.WAKE and self.anim_finished:
                if random.random() < 0.5: self.change_state(self.TELE_OUT)
                else: self._random_motion(); self.change_state(self.FLY)
                self.sleep_cooldown = random.randint(600, 1800)
            elif self.state is self.ANTIC:
                if self.no_target_attack:
                    if self.anim_finished: self.change_state(self.SHOOT)
                elif not self._target_alive(): self._on_target_lost()
                elif self.anim_finished: self.change_state(self.SHOOT)
            elif self.state is self.SHOOT and self.anim_finished:
                if self.no_target_attack:
                    self.owner.fireballs.append(Fireball(
                        QPointF(self.x, self.y), QPointF(self.x + 200 * self.direction, self.y),
                        owner=self, speed=self.owner.fireball_speed))
                    self.no_target_attack = False; self.attack_target = None
                elif self._target_alive():
                    self.owner.fireballs.append(Fireball(
                        QPointF(self.x, self.y), QPointF(self.attack_target.x, self.attack_target.y),
                        owner=self, speed=self.owner.fireball_speed))
                else: self._on_target_lost(); return
                self._random_motion(); self._just_changed_state = False
                self.change_state(self.pre_attack_state); self.attack_cooldown = 120
            elif self.state is self.BURST and self.anim_finished:
                if self.stage < 4: self.stage += 1
                self._apply_owner_hp(); self.growth_timer = random.randint(3750, 11250)
                self._random_motion(); self.change_state(self.FLY); self._battle_continue()

        if self._just_changed_state: self._just_changed_state = False
        else: self._advance_anim(3 if self.state in (self.TELE_OUT, self.TELE_IN) else 4)
        if self.pending_direction is not None:
            self.direction = self.pending_direction; self.pending_direction = None
        elif self.state is self.FLY and not self.hovering and self.vx != 0:
            self.direction = 1 if self.vx >= 0 else -1

    def _advance_anim(self, delay):
        if not self.anim_frames: return
        self.anim_timer += 1
        if self.anim_timer >= delay:
            self.anim_timer = 0
            if self.anim_loop: self.anim_idx = (self.anim_idx + 1) % len(self.anim_frames)
            elif self.anim_idx < len(self.anim_frames) - 1: self.anim_idx += 1
            else: self.anim_finished = True

    def _is_stationary(self): return abs(self.vx) < 0.1 and abs(self.vy) < 0.1

    def _update_timers(self):
        if self.state in (self.FLY, self.IDLE, self.TURN_TO_IDLE) and not self.battle_royale:
            self.teleport_timer -= 1
            if self.teleport_timer <= 0:
                self.vx = self.vy = 0; self.change_state(self.TELE_OUT)
                self.teleport_timer = random.randint(600, 1800); return
        if self.attack_cooldown > 0 and self.state not in (self.ANTIC, self.SHOOT) and self.attack_mode is None:
            self.attack_cooldown -= 1
        if self.state in (self.FLY, self.IDLE) and not self.hovering and not self.battle_royale:
            self.sleep_cooldown -= 1
            if self.sleep_cooldown <= 0: self.initiate_sleep()

    def initiate_sleep(self):
        self.vx = self.vy = 0; self._stop_fly_loop()
        rect = self.owner.screen_rect
        if random.random() < 0.5:
            self.target_sleep_y = rect.height() - 100; self.vy = 1.5
            self.state = self.FLY; self._update_anim(); self.sleep_pending = 'fly_to_bottom'
        else:
            self._teleport_target_x = max(100, min(rect.width() - 100, self.x))
            self._teleport_target_y = rect.height() - 100
            self._sleep_after_teleport = True; self.change_state(self.TELE_OUT)
        self.sleep_cooldown = random.randint(600, 1800)

class DeskPetWindow(QWidget):
    FLIP_X = QTransform().scale(-1, 1)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.screen_rect = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_rect)
        self.pets = []; self.fireballs = []
        self.dragging_pet = None; self.drag_offset = QPointF(0, 0); self.right_clicked_pet = None
        self.split_timer = 3750; self.auto_attack_timer = 3600
        self.split_limit = 4; self.fireball_speed = 12
        self.stage_hp = {1: 1, 2: 2, 3: 3, 4: 4}; self.battle_royale_global = False
        self.peace_mode = False
        first_pet = Pet(stage=1); first_pet.owner = self; first_pet._apply_owner_hp()
        self.pets.append(first_pet)
        self.timer = QTimer(self); self.timer.timeout.connect(self.game_loop); self.timer.start(16)
        self.init_tray()

    def init_tray(self):
        self.tray = QSystemTrayIcon(self); self.tray.setIcon(QIcon.fromTheme("face-smile"))
        menu = QMenu(); menu.addAction("退出", QApplication.quit)
        self.tray.setContextMenu(menu); self.tray.show()

    def _new_pet(self, stage, x, y):
        pet = Pet(stage=stage); pet.owner = self; pet._apply_owner_hp()
        pet.x, pet.y = x, y; pet.state = pet.TELE_IN; pet._update_anim(); return pet

    def _random_missing_stage(self):
        used = {p.stage for p in self.pets}
        missing = [s for s in range(1, 5) if s not in used]
        return random.choice(missing) if missing else random.randint(1, 4)

    def game_loop(self):
        for pet in self.pets:
            if pet.sleep_pending == 'fly_to_bottom' and pet.y >= pet.target_sleep_y:
                pet.y = pet.target_sleep_y; pet.vy = 0
                pet.change_state(pet.SLEEP_ANIM); pet.sleep_pending = None

        for pet in self.pets:
            if pet.pending_removal:
                pet._stop_fly_loop()
                for other in self.pets:
                    if other.attack_target is pet:
                        other.attack_target = None
                        if other.state in (other.ANTIC, other.SHOOT):
                            other._random_motion(); other.change_state(other.FLY)
                        if other.battle_royale: other._battle_continue()

        for pet in self.pets[:]:
            pet.update()
            if pet.pending_removal and pet.state is pet.TELE_OUT and pet.anim_finished:
                pet._stop_fly_loop(); self.pets.remove(pet)

        for fb in self.fireballs[:]:
            fb.update()
            if not fb.active: self.fireballs.remove(fb); continue
            for pet in self.pets:
                if fb.hit_check(pet): pet.hit(1, attacker=fb.owner); break

        if self.battle_royale_global:
            alive = [p for p in self.pets if not p.pending_removal]
            if len(alive) <= 1:
                self.battle_royale_global = False
                for p in alive: p.battle_royale = False

        self.handle_split(); self.handle_random_attack(); self.update()

    def handle_split(self):
        if self.battle_royale_global or len(self.pets) >= self.split_limit: return
        self.split_timer -= 1
        if self.split_timer <= 0:
            self.split_timer = 3750
            source = random.choice(self.pets)
            new_pet = self._new_pet(self._random_missing_stage(),
                                    source.x + random.randint(-60, 60),
                                    source.y + random.randint(-60, 60))
            self.pets.append(new_pet); source.attack_cooldown = max(source.attack_cooldown, 120)

    def handle_random_attack(self):
        if self.peace_mode or self.battle_royale_global or len(self.pets) < 2: return
        self.auto_attack_timer -= 1
        if self.auto_attack_timer <= 0:
            self.auto_attack_timer = 3600
            candidates = [p for p in self.pets
                          if p.state in (p.FLY, p.IDLE) and p.attack_cooldown <= 0
                          and not p.hovering and p.can_attack()]
            if candidates:
                attacker = random.choice(candidates)
                targets = [p for p in self.pets if p is not attacker]
                if targets: attacker._start_attack(random.choice(targets)); attacker.attack_cooldown = 120

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            clicked = next((p for p in self.pets if p.hit_test(event.pos())), None)
            if clicked:
                self.right_clicked_pet = clicked; clicked.hovering = True; clicked.vx = clicked.vy = 0
                if clicked.state not in (clicked.IDLE, clicked.SLEEP_ANIM, clicked.SLEEP_STILL):
                    clicked.change_state(clicked.IDLE)
                self.show_context_menu(clicked, event.globalPos())
                clicked.hovering = False
                if clicked.state is clicked.IDLE: clicked._random_motion(); clicked.change_state(clicked.FLY)
            else: self.lower()
        elif event.button() == Qt.LeftButton:
            if self.right_clicked_pet:
                rp = self.right_clicked_pet; self.right_clicked_pet = None
                if rp in self.pets and not rp.pending_removal:
                    rp.hovering = False
                    if rp.state is rp.IDLE: rp.change_state(rp.FLY)
                    rp._random_motion()
            for pet in self.pets:
                if pet.hit_test(event.pos()):
                    self.dragging_pet = pet
                    self.drag_offset = QPointF(pet.x - event.pos().x(), pet.y - event.pos().y())
                    pet.hovering = True; pet.vx = pet.vy = 0; break
        else: super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging_pet:
            pet = self.dragging_pet; margin = 80
            pet.x = max(margin, min(self.screen_rect.width() - margin,
                                    event.pos().x() + self.drag_offset.x()))
            pet.y = max(margin, min(self.screen_rect.height() - margin,
                                    event.pos().y() + self.drag_offset.y()))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging_pet:
            pet = self.dragging_pet; pet.hovering = False
            pet.change_state(pet.FLY); pet._random_motion(); self.dragging_pet = None

    def show_context_menu(self, pet, pos):
        menu = QMenu(self)
        menu.addAction("保留一个", lambda: self.retain_one(pet))
        stage_menu = menu.addMenu("生长阶段")
        stage_group = QActionGroup(stage_menu)
        for i in range(1, 5):
            action = QAction(f"阶段 {i}", stage_menu, checkable=True)
            if i == pet.stage: action.setChecked(True)
            action.triggered.connect(lambda checked, s=i: self.set_pet_stage(pet, s))
            stage_group.addAction(action); stage_menu.addAction(action)
        menu.addAction("休眠", lambda: self.sleep_pet(pet))
        menu.addAction("唤醒", lambda: self.wake_pet(pet))
        menu.addAction("分裂", lambda: self.split_pet(pet))
        menu.addAction("瞬移", lambda: self.teleport_pet(pet))
        if pet.can_attack(): menu.addAction("攻击", lambda: self.attack_from_menu(pet))
        if pet.can_attack(): menu.addAction("大乱斗", lambda: self.battle_royale_pet(pet))
        if len(self.pets) >= 2: menu.addAction("删除", lambda: self.delete_pet(pet))
        menu.addSeparator()
        settings = menu.addMenu("设置")
        settings.addAction(f"分裂上限 (当前: {self.split_limit})", lambda: self.set_split_limit())
        settings.addSeparator()
        settings.addAction(f"火球速度 (当前: {self.fireball_speed})", lambda: self.set_attack_speed())
        settings.addSeparator()
        for i in range(1, 5):
            settings.addAction(f"阶段{i}血量 (当前: {self.stage_hp.get(i, i)})",
                               lambda s=i: QTimer.singleShot(100, lambda: self.set_stage_hp(s)))
        settings.addSeparator()
        peace_menu = settings.addMenu("和平模式")
        peace_group = QActionGroup(peace_menu)
        peace_yes = QAction("是", peace_menu, checkable=True)
        peace_no = QAction("否", peace_menu, checkable=True)
        if self.peace_mode: peace_yes.setChecked(True)
        else: peace_no.setChecked(True)
        peace_yes.triggered.connect(lambda: self.set_peace_mode(True))
        peace_no.triggered.connect(lambda: self.set_peace_mode(False))
        peace_group.addAction(peace_yes); peace_menu.addAction(peace_yes)
        peace_group.addAction(peace_no); peace_menu.addAction(peace_no)
        menu.addSeparator()
        bgm = menu.addMenu("背景音乐")
        bgm_group = QActionGroup(bgm)
        for key, label in {'bgm_grimm': 'Grimm', 'bgm_epic': 'Grimm Epic Layer'}.items():
            action = QAction(label, bgm, checkable=True)
            if audio_manager and audio_manager.current_bgm == key: action.setChecked(True)
            action.triggered.connect(lambda checked, k=key: self.set_bgm(k))
            bgm_group.addAction(action); bgm.addAction(action)
        bgm.addSeparator()
        bgm.addAction("音量调节", self.manual_set_bgm_volume)
        bgm.addAction("关闭", self.stop_bgm)
        menu.addAction("停止音频" if (audio_manager and audio_manager.audio_enabled) else "开始音频",
                       self.toggle_audio)
        menu.addSeparator()
        menu.addAction("退出", QApplication.quit)
        menu.exec_(pos)

    def retain_one(self, pet):
        for p in self.pets[:]:
            if p is not pet: p._die(); p.pending_removal = True

    def set_pet_stage(self, pet, stage):
        if pet.stage != stage:
            pet.stage = stage; pet._apply_owner_hp(); pet._update_anim()
            pet.growth_timer = random.randint(3750, 11250)

    def wake_pet(self, pet):
        if pet.state in (pet.SLEEP_ANIM, pet.SLEEP_STILL):
            pet.hovering = False; pet.sleep_duration = 0
            if random.random() < 0.5: pet.change_state(pet.TELE_OUT)
            else: pet.change_state(pet.WAKE)
            pet.sleep_cooldown = random.randint(600, 1800)

    def sleep_pet(self, pet): pet.hovering = False; pet.initiate_sleep()

    def split_pet(self, pet):
        if len(self.pets) >= self.split_limit: return
        new_pet = self._new_pet(self._random_missing_stage(),
                                pet.x + random.randint(-60, 60),
                                pet.y + random.randint(-60, 60))
        self.pets.append(new_pet); pet.attack_cooldown = max(pet.attack_cooldown, 120)

    def teleport_pet(self, pet): pet.hovering = False; pet.change_state(pet.TELE_OUT)

    def attack_from_menu(self, pet):
        if self.peace_mode: return
        targets = [p for p in self.pets if p is not pet]
        if targets: pet._start_attack(random.choice(targets))
        else:
            pet.no_target_attack = True
            pet.pre_attack_state = pet.state if pet.state in (pet.FLY, pet.IDLE) else pet.FLY
            pet.vx = pet.vy = 0; pet.hovering = False; pet.change_state(pet.ANTIC)

    def battle_royale_pet(self, pet):
        if self.peace_mode: return
        alive = [p for p in self.pets if not p.pending_removal]
        if len(alive) < 2: return
        for p in alive:
            if p.stage < 2: p.stage = 2; p._apply_owner_hp(); p._update_anim()
            p.growth_timer = random.randint(3750, 11250)
            if p.state in (p.SLEEP_ANIM, p.SLEEP_STILL):
                p.hovering = False; p.sleep_duration = 0; p.change_state(p.WAKE)
            p.battle_royale = True; p._stop_fly_loop(); p.hovering = False; p.attack_cooldown = 0
        self.battle_royale_global = True
        for p in alive:
            targets = [t for t in alive if t is not p]
            if targets: p._start_attack(random.choice(targets))

    def delete_pet(self, pet): pet._die(); pet.pending_removal = True
    def set_bgm(self, key):
        if audio_manager: audio_manager.play_bgm(key)
    def stop_bgm(self):
        if audio_manager: audio_manager.stop_bgm()

    def manual_set_bgm_volume(self):
        if audio_manager:
            vol, ok = get_int_input("音量调节", "音量 (0-100):", audio_manager.bgm_volume, 0, 100, 5)
            if ok: audio_manager.set_bgm_volume(vol)

    def toggle_audio(self):
        if audio_manager: audio_manager.toggle_audio()

    def set_split_limit(self):
        val, ok = get_int_input("分裂上限", "分裂上限 (1-99999):", self.split_limit, 1, 99999)
        if ok: self.split_limit = val

    def set_attack_speed(self):
        val, ok = get_int_input("火球速度", "火球飞行速度 (1-999, 越大越快):", self.fireball_speed, 1, 999)
        if ok: self.fireball_speed = val

    def set_stage_hp(self, stage):
        val, ok = get_int_input(f"阶段{stage}血量", f"阶段{stage}血量 (1-99999):",
                                self.stage_hp.get(stage, stage), 1, 99999)
        if ok:
            self.stage_hp[stage] = val
            for pet in self.pets:
                if pet.stage == stage: pet._apply_owner_hp()

    def set_peace_mode(self, enable):
        self.peace_mode = enable
        if enable:
            for p in self.pets:
                p.battle_royale = False
                p.attack_target = None
                p.attack_mode = None
                p.attack_cooldown = 0
                p.no_target_attack = False
            self.battle_royale_global = False

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        for fb in self.fireballs:
            frame = fb.current_frame()
            if frame: painter.drawPixmap(int(fb.pos.x() - frame.width() // 2),
                                         int(fb.pos.y() - frame.height() // 2), frame)
        for pet in self.pets:
            frame = pet.current_frame()
            if frame:
                if pet.direction == -1: frame = frame.transformed(DeskPetWindow.FLIP_X)
                painter.drawPixmap(int(pet.x - frame.width() // 2),
                                   int(pet.y - frame.height() // 2), frame)

if __name__ == '__main__':
    app = QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Grimmchild Anim')
    try: load_animations(base_dir)
    except FileNotFoundError as e: print(e); sys.exit(1)
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'AudioClip')
    audio_manager = AudioManager(audio_dir)
    window = DeskPetWindow(); window.show()
    sys.exit(app.exec_())