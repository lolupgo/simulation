import pygame
import random

# --- Constants & Configuration ---
WIDTH, HEIGHT = 1200, 800
SIDEBAR_WIDTH = 300
NODE_RADIUS = 22
FPS = 60

# Colors (Dark Theme)
BG_COLOR = (30, 30, 30)
SIDEBAR_BG = (45, 45, 45)
TEXT_COLOR = (220, 220, 220)
EDGE_COLOR = (100, 100, 100)

# Node State Colors
COLOR_UNVISITED = (80, 80, 80)
COLOR_START = (0, 200, 0)
COLOR_GOAL = (200, 0, 0)
COLOR_CURRENT = (0, 255, 255)   # Cyan (Processing)
COLOR_FRONTIER = (255, 200, 0)  # Yellow (In Priority Queue)
COLOR_VISITED = (0, 100, 200)   # Blue (Done)
COLOR_PATH = (0, 255, 0)        # Bright Green

# --- Classes ---

class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.edges = []  # List of tuples: (child_node, weight)
        self.parent = None
        
        # UCS Specific Attributes
        self.g_cost = float('inf')  # Cost from start to this node
        
        # State
        self.state = 'unvisited' 
        self.is_start = False
        self.is_goal = False
        self.is_current = False
        self.in_final_path = False

    def reset(self):
        self.state = 'unvisited'
        self.parent = None
        self.g_cost = float('inf')
        self.is_current = False
        self.in_final_path = False

    def draw_edges(self, screen, font):
        for child, weight in self.edges:
            # Line Style
            color = EDGE_COLOR
            width = 2
            
            # Highlight path
            if self.in_final_path and child.in_final_path and child.parent == self:
                color = COLOR_PATH
                width = 5
            elif self.in_final_path and child.in_final_path and self.parent == child:
                # This handles the parent pointer visual for the reverse path
                color = COLOR_PATH
                width = 5

            pygame.draw.line(screen, color, (self.x, self.y), (child.x, child.y), width)
            
            # Draw Weight Text (midpoint)
            mid_x = (self.x + child.x) / 2
            mid_y = (self.y + child.y) / 2
            
            # Weight box background for readability
            weight_surf = font.render(str(weight), True, (255, 255, 0))
            rect = weight_surf.get_rect(center=(mid_x, mid_y))
            pygame.draw.rect(screen, BG_COLOR, rect.inflate(4, 4))
            screen.blit(weight_surf, rect)

    def draw_body(self, screen, font, small_font):
        color = COLOR_UNVISITED
        if self.in_final_path: color = COLOR_PATH
        elif self.is_current: color = COLOR_CURRENT
        elif self.is_start: color = COLOR_START
        elif self.is_goal: color = COLOR_GOAL
        elif self.state == 'frontier': color = COLOR_FRONTIER
        elif self.state == 'visited': color = COLOR_VISITED

        pygame.draw.circle(screen, color, (self.x, self.y), NODE_RADIUS)
        pygame.draw.circle(screen, (255, 255, 255), (self.x, self.y), NODE_RADIUS, 2)
        
        # Draw ID (Center)
        text = font.render(str(self.id), True, (255,255,255) if color != COLOR_CURRENT else (0,0,0))
        text_rect = text.get_rect(center=(self.x, self.y))
        screen.blit(text, text_rect)

        # Draw Current Cost g(n) (Top Right of node)
        if self.g_cost != float('inf'):
            cost_text = small_font.render(f"g:{self.g_cost}", True, (0, 255, 255))
            screen.blit(cost_text, (self.x + 10, self.y - 30))

class SearchTree:
    def __init__(self):
        self.nodes = []
        self.priority_queue = [] # List of nodes, sorted by g_cost
        self.start_node = None
        self.goal_node = None
        
        self.running = False
        self.completed = False
        self.message = "L-Click: Start | R-Click: Goal"

    def generate_tree(self):
        self.nodes = []
        root = Node(0, (WIDTH - SIDEBAR_WIDTH) // 2, 80)
        self.nodes.append(root)

        # (parent_node, x_min, x_max, depth)
        queue = [(root, 50, WIDTH - SIDEBAR_WIDTH - 50, 1)]
        count = 1
        max_depth = 5

        import collections
        gen_queue = collections.deque(queue)

        while gen_queue:
            parent, x_min, x_max, depth = gen_queue.popleft()
            if depth >= max_depth: continue

            num_children = random.choice([2, 3])
            if (x_max - x_min) < 60: num_children = 1 if random.random() > 0.5 else 0

            span = (x_max - x_min) / num_children if num_children > 0 else 0
            
            for i in range(num_children):
                child_x = x_min + span * i + span / 2
                child_y = 80 + depth * 120
                child = Node(count, int(child_x), int(child_y))
                
                # Assign Random Cost (Weight)
                weight = random.randint(1, 9)
                
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
                    self.reset_search()
                elif button == 3:
                    if self.goal_node: self.goal_node.is_goal = False
                    node.is_goal = True
                    self.goal_node = node
                    self.reset_search()
                return

    def reset_search(self):
        self.priority_queue = []
        self.running = False
        self.completed = False
        self.message = "Press SPACE to Step"
        for node in self.nodes:
            node.reset()
        
        if self.start_node and self.goal_node:
            self.start_node.g_cost = 0
            self.priority_queue.append(self.start_node)
            self.start_node.state = 'frontier'
            self.message = "Ready. Priority Queue Init. Press SPACE."

    def step(self):
        if not self.running and not self.completed:
            self.running = True
        if self.completed: return

        if not self.priority_queue:
            self.message = "Priority Queue Empty! Goal unreachable."
            self.completed = True
            return

        # 1. Pop node with Lowest Cost
        # Sort queue to simulate Priority Queue pop
        self.priority_queue.sort(key=lambda n: n.g_cost)
        current = self.priority_queue.pop(0)

        # Visual cleanup
        for n in self.nodes: 
            if n.is_current: n.is_current = False
        current.is_current = True
        current.state = 'visited'

        # 2. Check Goal
        if current == self.goal_node:
            self.completed = True
            self.message = f"Goal Found! Total Cost: {current.g_cost}"
            self.reconstruct_path(current)
            return

        # 3. Expand Neighbors
        updates = 0
        for child, weight in current.edges:
            new_cost = current.g_cost + weight
            
            if child.state == 'unvisited' and child not in self.priority_queue:
                child.g_cost = new_cost
                child.parent = current
                child.state = 'frontier'
                self.priority_queue.append(child)
                updates += 1
            elif child.state == 'frontier' or child.state == 'visited':
                # RELAXATION STEP: Check if we found a cheaper way
                if new_cost < child.g_cost:
                    child.g_cost = new_cost
                    child.parent = current
                    if child.state == 'visited':
                        child.state = 'frontier' # Re-evaluate if visited (optional in some implementations, but good for strict UCS)
                        self.priority_queue.append(child)
                    updates += 1
        
        # Sort again for visual consistency immediately
        self.priority_queue.sort(key=lambda n: n.g_cost)
        self.message = f" expanded Node {current.id} (g={current.g_cost}). Updated {updates} neighbors."

    def reconstruct_path(self, current):
        temp = current
        while temp:
            temp.in_final_path = True
            temp = temp.parent

# --- UI Functions ---

def draw_sidebar(screen, font, tree):
    rect = pygame.Rect(WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(screen, SIDEBAR_BG, rect)
    pygame.draw.line(screen, (100,100,100), (WIDTH - SIDEBAR_WIDTH, 0), (WIDTH - SIDEBAR_WIDTH, HEIGHT), 2)

    # Header
    title = font.render("UCS Simulation", True, (255, 255, 255))
    screen.blit(title, (WIDTH - SIDEBAR_WIDTH + 20, 20))
    
    sub = pygame.font.SysFont('arial', 16).render("Uniform Cost Search", True, (150, 150, 150))
    screen.blit(sub, (WIDTH - SIDEBAR_WIDTH + 20, 50))

    # Legend
    y_offset = 90
    small_font = pygame.font.SysFont('arial', 18)
    legend = [("Start", COLOR_START), ("Goal", COLOR_GOAL), 
              ("Current", COLOR_CURRENT), ("PriorityQ", COLOR_FRONTIER)]
    
    for text, color in legend:
        pygame.draw.circle(screen, color, (WIDTH - SIDEBAR_WIDTH + 30, y_offset + 10), 8)
        label = small_font.render(text, True, TEXT_COLOR)
        screen.blit(label, (WIDTH - SIDEBAR_WIDTH + 50, y_offset))
        y_offset += 30
        
    y_offset += 20
    
    # Priority Queue List
    pq_title = font.render("Priority Queue", True, (255, 255, 255))
    screen.blit(pq_title, (WIDTH - SIDEBAR_WIDTH + 20, y_offset))
    y_offset += 30
    
    sub_pq = small_font.render("(Sorted by Cost)", True, (150, 150, 150))
    screen.blit(sub_pq, (WIDTH - SIDEBAR_WIDTH + 20, y_offset))
    y_offset += 30

    # Draw Queue Items (Vertical List for details)
    for i, node in enumerate(tree.priority_queue):
        if i > 12: break
        
        # Row Background
        row_color = (60, 60, 60)
        pygame.draw.rect(screen, row_color, (WIDTH - SIDEBAR_WIDTH + 10, y_offset, SIDEBAR_WIDTH - 20, 25))
        
        # Text: Node ID -> Cost
        row_text = small_font.render(f"Node {node.id} : Cost {node.g_cost}", True, COLOR_FRONTIER)
        screen.blit(row_text, (WIDTH - SIDEBAR_WIDTH + 20, y_offset + 2))
        
        y_offset += 28

    # Status Message
    y_offset = max(y_offset + 20, 600)
    pygame.draw.rect(screen, (20, 20, 20), (WIDTH - SIDEBAR_WIDTH + 10, y_offset, SIDEBAR_WIDTH - 20, 80))
    
    words = tree.message.split(' ')
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        if len(' '.join(curr)) > 25:
            lines.append(' '.join(curr[:-1]))
            curr = [w]
    lines.append(' '.join(curr))
    
    for i, line in enumerate(lines):
        msg = small_font.render(line, True, (0, 255, 255))
        screen.blit(msg, (WIDTH - SIDEBAR_WIDTH + 20, y_offset + 10 + i * 20))

    # Controls
    ctrl_y = HEIGHT - 100
    ctrl_txt = small_font.render("Space: Step | R: Reset | N: New Tree", True, (150,150,150))
    screen.blit(ctrl_txt, (WIDTH - SIDEBAR_WIDTH + 20, ctrl_y))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Uniform Cost Search Visualization")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont('arial', 22, bold=True)
    small_font = pygame.font.SysFont('arial', 16)
    edge_font = pygame.font.SysFont('arial', 14, bold=True)

    tree = SearchTree()
    tree.generate_tree()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not tree.running and not tree.completed:
                    tree.handle_click(pygame.mouse.get_pos(), event.button)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if tree.start_node and tree.goal_node:
                        tree.step()
                elif event.key == pygame.K_r:
                    tree.reset_search()
                elif event.key == pygame.K_n:
                    tree.generate_tree()
                    tree.reset_search()

        screen.fill(BG_COLOR)
        
        # Draw Edges first
        for node in tree.nodes:
            node.draw_edges(screen, edge_font)
            
        # Draw Nodes
        for node in tree.nodes:
            node.draw_body(screen, font, small_font)

        draw_sidebar(screen, font, tree)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()