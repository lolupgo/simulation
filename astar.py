import pygame
import random
import math

# --- Constants ---
WIDTH, HEIGHT = 1200, 800
SIDEBAR_WIDTH = 350 # Wider for F/G/H data
NODE_RADIUS = 25
FPS = 60

# Colors
BG_COLOR = (30, 30, 30)
SIDEBAR_BG = (45, 45, 45)
TEXT_COLOR = (220, 220, 220)
EDGE_COLOR = (100, 100, 100)

COLOR_START = (0, 200, 0)
COLOR_GOAL = (200, 0, 0)
COLOR_CURRENT = (0, 255, 255) 
COLOR_FRONTIER = (255, 200, 0)
COLOR_VISITED = (0, 100, 200)
COLOR_PATH = (0, 255, 0)

# --- Classes ---
class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.edges = [] 
        self.parent = None
        
        # A* Metrics
        self.g = float('inf') # Cost from start
        self.h = 0            # Heuristic to goal
        self.f = float('inf') # Total estimated cost (g+h)
        
        self.state = 'unvisited' 
        self.is_start = False
        self.is_goal = False
        self.is_current = False
        self.in_final_path = False

    def reset(self):
        self.state = 'unvisited'
        self.parent = None
        self.g = float('inf')
        self.h = 0
        self.f = float('inf')
        self.is_current = False
        self.in_final_path = False

    def calculate_heuristic(self, goal_node):
        # Euclidean distance, scaled down to match edge weights roughly
        dist = math.sqrt((self.x - goal_node.x)**2 + (self.y - goal_node.y)**2)
        self.h = round(dist / 15.0, 1) # Scaling factor for visual balance

    def draw_edges(self, screen, font):
        for child, weight in self.edges:
            color = EDGE_COLOR
            width = 2
            if self.in_final_path and child.in_final_path and (child.parent == self or self.parent == child):
                color = COLOR_PATH
                width = 5

            pygame.draw.line(screen, color, (self.x, self.y), (child.x, child.y), width)
            
            mid_x = (self.x + child.x) / 2
            mid_y = (self.y + child.y) / 2
            weight_surf = font.render(str(weight), True, (255, 255, 0))
            rect = weight_surf.get_rect(center=(mid_x, mid_y))
            pygame.draw.rect(screen, BG_COLOR, rect.inflate(4, 4))
            screen.blit(weight_surf, rect)

    def draw_body(self, screen, font, detail_font):
        color = (80, 80, 80)
        if self.in_final_path: color = COLOR_PATH
        elif self.is_current: color = COLOR_CURRENT
        elif self.is_start: color = COLOR_START
        elif self.is_goal: color = COLOR_GOAL
        elif self.state == 'frontier': color = COLOR_FRONTIER
        elif self.state == 'visited': color = COLOR_VISITED

        pygame.draw.circle(screen, color, (self.x, self.y), NODE_RADIUS)
        pygame.draw.circle(screen, (255, 255, 255), (self.x, self.y), NODE_RADIUS, 2)
        
        # ID
        text = font.render(str(self.id), True, (255,255,255) if color != COLOR_CURRENT else (0,0,0))
        screen.blit(text, text.get_rect(center=(self.x, self.y)))

        # Draw F, G, H if visited or frontier
        if self.state in ['frontier', 'visited'] or self.is_current:
            # F on top
            f_txt = detail_font.render(f"F:{self.f:.1f}", True, (0, 255, 255))
            screen.blit(f_txt, (self.x - 25, self.y - 45))
            # G and H below
            gh_txt = detail_font.render(f"g:{self.g:.1f} h:{self.h:.1f}", True, (200, 200, 200))
            screen.blit(gh_txt, (self.x - 35, self.y + 30))


class SearchTree:
    def __init__(self):
        self.nodes = []
        self.open_list = [] # The Priority Queue
        self.start_node = None
        self.goal_node = None
        self.running = False
        self.completed = False
        self.message = "L-Click: Start | R-Click: Goal"

    def generate_tree(self):
        # (Similar generation to UCS)
        self.nodes = []
        root = Node(0, (WIDTH - SIDEBAR_WIDTH) // 2, 80)
        self.nodes.append(root)
        queue = [(root, 50, WIDTH - SIDEBAR_WIDTH - 50, 1)]
        count = 1
        import collections
        gen_queue = collections.deque(queue)
        while gen_queue:
            parent, x_min, x_max, depth = gen_queue.popleft()
            if depth >= 5: continue
            num_children = random.choice([2, 3])
            if (x_max - x_min) < 70: num_children = 1 if random.random() > 0.6 else 0
            span = (x_max - x_min) / num_children if num_children > 0 else 0
            for i in range(num_children):
                child_x = x_min + span * i + span / 2
                child_y = 80 + depth * 120
                child = Node(count, int(child_x), int(child_y))
                weight = random.randint(1, 5) # Smaller weights for A* demo
                self.nodes.append(child)
                parent.edges.append((child, weight))
                gen_queue.append((child, x_min + span * i, x_min + span * (i+1), depth + 1))
                count += 1

    def handle_click(self, pos, button):
        x, y = pos
        for node in self.nodes:
            if ((x - node.x)**2 + (y - node.y)**2)**0.5 < NODE_RADIUS:
                if button == 1:
                    if self.start_node: self.start_node.is_start = False
                    node.is_start = True
                    self.start_node = node
                elif button == 3:
                    if self.goal_node: self.goal_node.is_goal = False
                    node.is_goal = True
                    self.goal_node = node
                self.reset_search()
                return

    def reset_search(self):
        self.open_list = []
        self.running = False
        self.completed = False
        self.message = "Press SPACE to Step"
        for node in self.nodes:
            node.reset()
        
        if self.start_node and self.goal_node:
            # 1. Calculate Heuristics for ALL nodes first
            for n in self.nodes:
                n.calculate_heuristic(self.goal_node)
            
            # 2. Init Start Node
            self.start_node.g = 0
            self.start_node.f = self.start_node.g + self.start_node.h
            self.open_list.append(self.start_node)
            self.start_node.state = 'frontier'
            self.message = "Heuristics calculated. Open List Init. Press SPACE."

    def step(self):
        if not self.running and not self.completed: self.running = True
        if self.completed or not self.open_list:
             if not self.open_list and not self.completed: self.message = "No Path Found."
             self.completed = True
             return

        # 1. Pop node with Lowest F Score
        self.open_list.sort(key=lambda n: n.f)
        current = self.open_list.pop(0)

        for n in self.nodes: n.is_current = False
        current.is_current = True
        current.state = 'visited'

        # 2. Check Goal
        if current == self.goal_node:
            self.completed = True
            self.message = f"Goal Found! Final Cost: {current.g}"
            self.reconstruct_path(current)
            return

        # 3. Expand Neighbors
        updates = 0
        for child, weight in current.edges:
            tentative_g = current.g + weight
            
            if tentative_g < child.g:
                # Found a better path to child
                child.parent = current
                child.g = tentative_g
                child.f = child.g + child.h
                
                if child.state == 'unvisited':
                    child.state = 'frontier'
                    self.open_list.append(child)
                    updates += 1
                elif child.state == 'frontier':
                     # It's already in open list, but we updated its F, need resort later
                     updates += 1
                     pass
        
        self.open_list.sort(key=lambda n: n.f) # Ensure sorted for UI
        self.message = f"Expanded Node {current.id} (F:{current.f:.1f}). Updated {updates} neighbors."

    def reconstruct_path(self, current):
        temp = current
        while temp:
            temp.in_final_path = True
            temp = temp.parent

# --- UI ---
def draw_sidebar(screen, font, small_font, tree):
    rect = pygame.Rect(WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(screen, SIDEBAR_BG, rect)
    pygame.draw.line(screen, (100,100,100), (WIDTH - SIDEBAR_WIDTH, 0), (WIDTH - SIDEBAR_WIDTH, HEIGHT), 2)

    title = font.render("A* Search Simulation", True, (255, 255, 255))
    screen.blit(title, (WIDTH - SIDEBAR_WIDTH + 20, 20))
    sub = small_font.render("f(n) = g(n) + h(n)", True, COLOR_CURRENT)
    screen.blit(sub, (WIDTH - SIDEBAR_WIDTH + 20, 55))

    # Legend (Simplified)
    y_off = 100
    legend = [("Start", COLOR_START), ("Goal", COLOR_GOAL), ("Open List", COLOR_FRONTIER)]
    for txt, col in legend:
        pygame.draw.circle(screen, col, (WIDTH - SIDEBAR_WIDTH + 30, y_off+10), 8)
        screen.blit(small_font.render(txt, True, TEXT_COLOR), (WIDTH - SIDEBAR_WIDTH + 50, y_off))
        y_off += 30

    # Priority Queue
    y_off += 20
    screen.blit(font.render("Open List (Sorted by F)", True, (255, 255, 255)), (WIDTH - SIDEBAR_WIDTH + 20, y_off))
    y_off += 40
    
    for i, node in enumerate(tree.open_list):
        if i > 10: break
        pygame.draw.rect(screen, (60,60,60), (WIDTH - SIDEBAR_WIDTH + 10, y_off, SIDEBAR_WIDTH - 20, 30))
        txt = small_font.render(f"ID:{node.id} | F:{node.f:.1f} (g:{node.g:.1f}+h:{node.h:.1f})", True, COLOR_FRONTIER)
        screen.blit(txt, (WIDTH - SIDEBAR_WIDTH + 20, y_off + 5))
        y_off += 35

    # Status
    y_off = HEIGHT - 150
    pygame.draw.rect(screen, (20,20,20), (WIDTH-SIDEBAR_WIDTH+10, y_off, SIDEBAR_WIDTH-20, 60))
    screen.blit(small_font.render(tree.message, True, COLOR_CURRENT), (WIDTH-SIDEBAR_WIDTH+20, y_off+20))
    screen.blit(small_font.render("Space: Step | R: Reset | N: New Tree", True, (150,150,150)), (WIDTH-SIDEBAR_WIDTH+20, HEIGHT-50))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("A* Search Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 22, bold=True)
    small_font = pygame.font.SysFont('arial', 16)
    detail_font = pygame.font.SysFont('arial', 12)

    tree = SearchTree()
    tree.generate_tree()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not tree.running: tree.handle_click(pygame.mouse.get_pos(), event.button)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and tree.start_node and tree.goal_node: tree.step()
                elif event.key == pygame.K_r: tree.reset_search()
                elif event.key == pygame.K_n: 
                    tree.generate_tree()
                    tree.start_node = None
                    tree.goal_node = None
                    tree.reset_search()

        screen.fill(BG_COLOR)
        for node in tree.nodes: node.draw_edges(screen, font)
        for node in tree.nodes: node.draw_body(screen, font, detail_font)
        draw_sidebar(screen, font, small_font, tree)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__": main()