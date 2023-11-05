import time
import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple
from random import randint
from pyscript import document, window, display
from js import Image
from pyodide.ffi import create_proxy

# -- Model

class GameStatus(Enum): 
    STARTING = 1
    RUNNING = 2
    END = 3

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    STANDING = 5

@dataclass
class Touches:
    last_xy : Tuple[float, float]
    diff_xy : Tuple[float, float]

@dataclass
class Player:
    image: Image
    frame: int
    animation_frames: int
    default_animation_frames: int
    direction: Direction
    frame_sets: Dict[Direction, List [str]]
    x: int
    y: int

@dataclass
class Apple:
    image: Image
    x: int
    y: int
    size: int

@dataclass
class Rectangle:
    x : int
    y : int
    width : int
    height :  int
    color : str
    speed : float

@dataclass
class Model:
    canvas: object
    width: int
    height: int
    context: object
    images: Dict[str, Image]
    status: GameStatus
    touches: Touches
    score: int
    time: int
    view_score_time: bool
    end_time: float
    player: Player
    apple: Apple
    rectangles: List[Rectangle]
    speed: int

# -- init

def get_image(name:str, model:Model)->Image:
    if name in model.images:
        return model.images[name]
    else:
        image = Image.new()
        image.src = f'./images/{name}'
        return image


def init_player(model:Model) -> Player:
    image = get_image('player_23.png', model)

    standing_frames = ['player_23.png']
    up_frames = ['player_03.png', 'player_04.png']
    down_frames = ['player_01.png', 'player_24.png']
    left_frames = ['player_14.png', 'player_15.png']
    right_frames = ['player_11.png', 'player_12.png']

    frame_sets = {
        Direction.STANDING: standing_frames,
        Direction.UP: up_frames,
        Direction.DOWN: down_frames,
        Direction.LEFT: left_frames,
        Direction.RIGHT: right_frames
    }

    default_animation_frames = 20

    return Player(
                frame = 0,
                image = image,
                animation_frames = default_animation_frames,
                default_animation_frames = default_animation_frames,
                direction = Direction.STANDING,
                frame_sets = frame_sets,
                x = model.canvas.width / 2 - image.width / 2,
                y = model.canvas.height / 2 - image.height / 2
            )


def init_apple(model:Model) -> Apple:
    image = get_image('apple.png', model)

    return Apple(
                image=image,
                x=randint(0,model.width),
                y=randint(0,model.height),
                size=64
           )

def init_rectangles(model:Model) -> List[Rectangle]:
    rectangles = []

    for i in range(40):
        color = f'rgb({randint(0,255)},{randint(0,255)},{randint(0,255)})'
        rectangles.append(Rectangle(
                            x = randint(0,model.width),
                            y = randint(0, model.height),
                            width = randint(0,100),
                            height = randint(0,100),
                            color = color,
                            speed = randint(1, 6)))

    return rectangles

def init() -> Model:
    canvas = document.getElementById('Canvas')
    canvas.width = 800
    canvas.height = 500

    context = canvas.getContext('2d')

    touches = Touches(last_xy=None,
                      diff_xy=None
                      )
    
    model = Model(canvas    = canvas,
                    width     = canvas.width,
                    height    = canvas.height,
                    context   = context,
                    images    = {},
                    status    = GameStatus.STARTING,
                    score     = 0,
                    time      = 60,
                    view_score_time = True,
                    touches = touches,
                    player    = None,
                    apple     = None,
                    rectangles= None,
                    end_time  = None,
                    speed     = 1
    )

    model.player = init_player(model)
    model.apple = init_apple(model)
    model.rectangles = init_rectangles(model)

    return model

# -- view

def view_player(m:Model)->None:
    m.context.drawImage(m.player.image,m.player.x,m.player.y)

    m.player.animation_frames -=1

    if m.player.animation_frames <= 0:
        m.player.animation_frames = m.player.default_animation_frames

        m.player.frame = (m.player.frame + 1) % len(m.player.frame_sets[m.player.direction])
        m.player.image = get_image(m.player.frame_sets[m.player.direction][m.player.frame],m)


def view_apple(m:Model)->None:
    m.context.drawImage(m.apple.image,m.apple.x,m.apple.y)


def view_rectangles(m:Model, rectangles:List[Rectangle])->None:
    for i in rectangles:
        m.context.fillStyle = i.color;
        m.context.fillRect(i.x, i.y, i.width, i.height)


def view_message(m:Model)->None:
    message = ""

    match m.status:
        case GameStatus.STARTING:
            message = "Press any key or touch to start"
        case GameStatus.END:
            message = "Game ended"

    if len(message)>0:
        m.context.font = "40px monospace"
        m.context.fillStyle = "black"
        m.context.textAlign = "center"
        m.context.fillText(message, m.width/2, m.height/2)
        m.context.shadowColor = "white"
        m.context.shadowOffsetX = 0
        m.context.shadowOffsetY = 0
        m.context.shadowBlur = 10

def view_score_time(m:Model)->None:
    if m.view_score_time:
        m.view_score_time = False
        document.getElementById("score_time").innerText = f'score: {m.score}    time: {m.time}'

def view(m:Model)->None:
    try:
        m.context.clearRect(0, 0, m.width, m.height)
        view_rectangles(m, m.rectangles[:20])
        view_player(m)
        view_apple(m)
        view_rectangles(m, m.rectangles[20:])
        view_message(m)
        view_score_time(m)
    except Exception as error:
        display(f"view An exception occurred: {error}")


# -- input

def change_game_state_starting():
    model.status = GameStatus.RUNNING
    model.end_time = time.time() + 60

def input_keyboard_down(event)->None:
    if model.status == GameStatus.STARTING:
        change_game_state_starting()
            
    match event.key:
        case 'ArrowLeft':
            model.player.direction = Direction.LEFT
        case 'ArrowRight':
            model.player.direction = Direction.RIGHT
        case 'ArrowUp':
            model.player.direction = Direction.UP
        case 'ArrowDown':
            model.player.direction = Direction.DOWN
        case _:
            model.player.direction = Direction.STANDING


def input_keyboard_up(event)->None:
    model.player.direction = Direction.STANDING

def input_touch_start(event)->None:
    try:
        rect = model.canvas.getBoundingClientRect()
        touch_x = event.touches.item(0).clientX - rect.left
        touch_y = event.touches.item(0).clientY - rect.top
        model.touches.last_xy = (touch_x,touch_y)
        model.touches.diff_xy = (0,0)
    
    except Exception as error:
        display(f"input_touch_start An exception occurred: {error}")

def input_touch_move(event)->None:
    rect = model.canvas.getBoundingClientRect()
    touch_x = event.touches.item(0).clientX - rect.left 
    touch_y = event.touches.item(0).clientY - rect.top

    model.touches.diff_xy = (model.touches.last_xy[0]-touch_x,
                             model.touches.last_xy[1]-touch_y)
    model.touches.last_xy = (touch_x,touch_y)
    (x, y) = model.touches.diff_xy
    #display(f"touch {x} {x} -")
    

def input_touch_end(event)->None:
    model.touches.last_xy = None
    model.touches.diff_xy = None
    model.player.direction = Direction.STANDING

# -- update

def update_player(m:Model)->None:
    try:
        if not m.touches.last_xy is None:
            (dx, dy) = m.touches.diff_xy
            if abs(dx) >= abs(dy):
                if dx < 0:
                    m.player.direction = Direction.RIGHT
                else:
                    m.player.direction = Direction.LEFT
            else:
                if dy > 0:
                    m.player.direction = Direction.UP
                else:
                    m.player.direction = Direction.DOWN
    
        match m.player.direction:
            case Direction.DOWN:
                m.player.y += m.speed   
            case Direction.UP:
                m.player.y -= m.speed  
            case Direction.RIGHT:
                m.player.x += m.speed   
            case Direction.LEFT:
                m.player.x -= m.speed
    except Exception as error:
        display(f"update_player An exception occurred: {error}")


def update_time(m:Model)->None:
    try:
        if time.time() < m.end_time:
            remaining_seconds = int(m.end_time - time.time())
            if remaining_seconds != m.time:
                m.time = remaining_seconds
                m.view_score_time = True
        else:
            m.status = GameStatus.END
    except Exception as error:
        display(f"update_time An exception occurred: {error}")


def update(m:Model)->None:
    try:
        match m.status:
            case GameStatus.STARTING:
                if not m.touches.last_xy is None:
                    change_game_state_starting()
            case GameStatus.RUNNING:
                update_time(m)
                update_player(m)

        touching =  (abs((m.player.x - m.apple.x)) < m.apple.size and
                        abs((m.player.y - m.apple.y)) < m.apple.size)
        
        if touching:
            m.apple.x=randint(0,m.width)
            m.apple.y=randint(0,m.height)
            m.score += 1
            m.view_score_time = True

        for i in m.rectangles:
            i.y += i.speed
            if i.y > m.height:
                i.y = -10

    except Exception as error:
        display(f"update An exception occurred: {error}")

# -- main

def do_loop(*args):
    update(model)
    view(model)
    window.requestAnimationFrame(create_proxy(do_loop))


model:Model = init()

document.addEventListener('keydown', create_proxy(input_keyboard_down))
document.addEventListener('keyup', create_proxy(input_keyboard_up))
document.addEventListener('touchstart', create_proxy(input_touch_start))
document.addEventListener('touchmove', create_proxy(input_touch_move))
document.addEventListener('touchend', create_proxy(input_touch_end))
                        
do_loop()

        #     canvas.addEventListener('mousedown', function(event) {
        #         const rect = canvas.getBoundingClientRect();
        #         const mouseX = event.clientX - rect.left;
        #         const mouseY = event.clientY - rect.top;

        #         if (mouseX >= square.x && mouseX <= square.x + square.size &&
        #             mouseY >= square.y && mouseY <= square.y + square.size) {
        #             let isDragging = true;
                    
        #             document.addEventListener('mousemove', function(event) {
        #                 if (isDragging) {
        #                     const newMouseX = event.clientX - rect.left;
        #                     const newMouseY = event.clientY - rect.top;
        #                     square.x = newMouseX - square.size/2;
        #                     square.y = newMouseY - square.size/2;
        #                 }
        #             });

        #             document.addEventListener('mouseup', function() {
        #                 isDragging = false;
        #             });
        #         }
        #     });

        #     canvas.addEventListener('touchstart', function(event) {
        #         const rect = canvas.getBoundingClientRect();
        #         const touchX = event.touches[0].clientX - rect.left;
        #         const touchY = event.touches[0].clientY - rect.top;

        #         if (touchX >= square.x && touchX <= square.x + square.size &&
        #             touchY >= square.y && touchY <= square.y + square.size) {
        #             let isDragging = true;
                    
        #             document.addEventListener('touchmove', function(event) {
        #                 if (isDragging) {
        #                     const newTouchX = event.touches[0].clientX - rect.left;
        #                     const newTouchY = event.touches[0].clientY - rect.top;
        #                     square.x = newTouchX - square.size/2;
        #                     square.y = newTouchY - square.size/2;
        #                 }
        #             });

        #             document.addEventListener('touchend', function() {
        #                 isDragging = false;
        #             });
        #         }
        #     });
        # });