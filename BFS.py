import pygame
import collections
import random

# --- Constants & Configuration ---
WIDTH, HEIGHT = 1200, 800
SIDEBAR_WIDTH = 300
NODE_RADIUS = 20
LAYER_HEIGHT = 100
FPS = 60

# Colors (Dark Theme)
BG_COLOR = (30, 30, 30)         # Dark Grey Background
SIDEBAR_BG = (50, 50, 50)       # Slightly lighter for sidebar
TEXT_COLOR = (220, 220, 220)
EDGE_COLOR = (100, 100, 100)

# Node State Colors
COLOR_UNVISITED = (80, 80, 80)  # Dark Grey
COLOR_START = (0, 200, 0)       # Green
COLOR_GOAL = (200, 0, 0)        # Red
COLOR_CURRENT = (0, 255, 255)   # Cyan (Processing now)
COLOR_FRONTIER = (255, 200, 0)  # Yellow (In Queue)
COLOR_VISITED = (0, 100, 200)   # Blue (Done)
COLOR_PATH = (0, 255, 0)        # Bright Green (Final Path)

# --- Classes ---

class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.children = []
        self.parent = None  # To reconstruct path
        
        # State: 'unvisited', 'frontier', 'visited'
        self.state = 'unvisited' 
        self.is_start = False
        self.is_goal = False
        self.is_current = False
        self.in_final_path = False

    def draw(self, screen, font):
        # Determine color based on priority
        color = COLOR_UNVISITED
        
        if self.in_final_path:
            color = COLOR_PATH
        elif self.is_current:
            color = COLOR_CURRENT
        elif self.is_start:
            color = COLOR_START
        elif self.is_goal:
            color = COLOR_GOAL
        elif self.state == 'frontier':
            color = COLOR_FRONTIER
        elif self.state == 'visited':
            color = COLOR_VISITED

        # Draw connection lines (Edges)
        for child in self.children:
            # Line color logic: highlight if part of final path
            line_color = EDGE_COLOR
            if self.in_final_path and child.in_final_path and child.parent == self:
                line_color = COLOR_PATH
                width = 4
            else:
                width = 2
            pygame.draw.line(screen, line_color, (self.x, self.y), (child.x, child.y), width)

    def draw_node_body(self, screen, font):
        # We draw the body separately so it sits on top of lines
        color = COLOR_UNVISITED
        if self.in_final_path: color = COLOR_PATH
        elif self.is_current: color = COLOR_CURRENT
        elif self.is_start: color = COLOR_START
        elif self.is_goal: color = COLOR_GOAL
        elif self.state == 'frontier': color = COLOR_FRONTIER
        elif self.state == 'visited': color = COLOR_VISITED

        pygame.draw.circle(screen, color, (self.x, self.y), NODE_RADIUS)
        pygame.draw.circle(screen, (255, 255, 255), (self.x, self.y), NODE_RADIUS, 2) # Border
        
        # Draw ID
        text = font.render(str(self.id), True, (255,255,255) if color != COLOR_CURRENT else (0,0,0))
        text_rect = text.get_rect(center=(self.x, self.y))
        screen.blit(text, text_rect)

    def reset(self):
        self.state = 'unvisited'
        self.parent = None
        self.is_current = False
        self.in_final_path = False
        # Note: We do not reset is_start or is_goal here typically, unless full reset

class SearchTree:
    def __init__(self):
        self.nodes = []
        self.root = None
        self.start_node = None
        self.goal_node = None
        
        # BFS Execution State
        self.queue = collections.deque()
        self.running = False
        self.completed = False
        self.found = False
        self.message = "Select Start (L-Click) & Goal (R-Click)"

    def generate_tree(self):
        """Generates a balanced-ish tree structure for visualization."""
        self.nodes = []
        # Hardcoded structure to ensure it looks good on screen
        # Levels: y = 100, 200, 300...
        # Root
        root = Node(0, (WIDTH - SIDEBAR_WIDTH) // 2, 80)
        self.nodes.append(root)
        self.root = root

        # Helper queue for generation: (parent_node, x_min, x_max, depth)
        gen_queue = collections.deque([(root, 50, WIDTH - SIDEBAR_WIDTH - 50, 1)])
        
        count = 1
        max_depth = 5

        while gen_queue:
            parent, x_min, x_max, depth = gen_queue.popleft()
            if depth >= max_depth:
                continue

            # Determine number of children (random 1 to 3)
            num_children = random.choice([2, 3])
            # If space is tight, reduce children
            if (x_max - x_min) < 60:
                num_children = 1 if random.random() > 0.5 else 0

            span = (x_max - x_min) / num_children if num_children > 0 else 0
            
            for i in range(num_children):
                child_x = x_min + span * i + span / 2
                child_y = 80 + depth * 120
                
                child = Node(count, int(child_x), int(child_y))
                self.nodes.append(child)
                parent.children.append(child)
                
                gen_queue.append((child, x_min + span * i, x_min + span * (i+1), depth + 1))
                count += 1

    def handle_click(self, pos, button):
        """
        Button 1: Left Click (Set Start)
        Button 3: Right Click (Set Goal)
        """
        x, y = pos
        # Check collision with nodes
        for node in self.nodes:
            distance = ((x - node.x)**2 + (y - node.y)**2)**0.5
            if distance < NODE_RADIUS:
                if button == 1: # Left Click -> Start
                    if self.start_node: self.start_node.is_start = False
                    node.is_start = True
                    self.start_node = node
                    self.reset_search()
                elif button == 3: # Right Click -> Goal
                    if self.goal_node: self.goal_node.is_goal = False
                    node.is_goal = True
                    self.goal_node = node
                    self.reset_search()
                return

    def reset_search(self):
        self.queue.clear()
        self.running = False
        self.completed = False
        self.found = False
        self.message = "Press SPACE to Step, 'R' to Full Reset"
        for node in self.nodes:
            node.reset()
        
        if self.start_node and self.goal_node:
            self.queue.append(self.start_node)
            self.start_node.state = 'frontier'
            self.message = "Ready. Queue initialized. Press SPACE."

    def step(self):
        if not self.running and not self.completed:
            self.running = True
        
        if self.completed:
            return

        if not self.queue:
            self.message = "Queue Empty! Goal not found."
            self.completed = True
            return

        # 1. Dequeue
        current = self.queue.popleft()
        
        # Reset previous current highlights
        for n in self.nodes:
            if n.is_current: n.is_current = False
            
        current.is_current = True
        current.state = 'visited'

        # 2. Check Goal
        if current == self.goal_node:
            self.found = True
            self.completed = True
            self.message = "Goal Found! Path reconstructed."
            self.reconstruct_path(current)
            return

        # 3. Enqueue Children
        added_count = 0
        for child in current.children:
            if child.state == 'unvisited' and child not in self.queue:
                child.state = 'frontier'
                child.parent = current
                self.queue.append(child)
                added_count += 1
        
        self.message = f"Visited Node {current.id}. Added {added_count} neighbors."

    def reconstruct_path(self, current):
        temp = current
        while temp:
            temp.in_final_path = True
            temp = temp.parent


# --- Main Application ---

def draw_sidebar(screen, font, tree):
    # Sidebar Background
    rect = pygame.Rect(WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(screen, SIDEBAR_BG, rect)
    pygame.draw.line(screen, (100,100,100), (WIDTH - SIDEBAR_WIDTH, 0), (WIDTH - SIDEBAR_WIDTH, HEIGHT), 2)

    # Title
    title = font.render("BFS Simulation", True, (255, 255, 255))
    screen.blit(title, (WIDTH - SIDEBAR_WIDTH + 20, 20))

    # Legend
    y_offset = 70
    legend_items = [
        ("Start Node", COLOR_START),
        ("Goal Node", COLOR_GOAL),
        ("Current (Processing)", COLOR_CURRENT),
        ("Frontier (In Queue)", COLOR_FRONTIER),
        ("Visited", COLOR_VISITED),
        ("Unvisited", COLOR_UNVISITED)
    ]
    
    small_font = pygame.font.SysFont('arial', 18)
    for text, color in legend_items:
        pygame.draw.circle(screen, color, (WIDTH - SIDEBAR_WIDTH + 30, y_offset + 10), 8)
        label = small_font.render(text, True, TEXT_COLOR)
        screen.blit(label, (WIDTH - SIDEBAR_WIDTH + 50, y_offset))
        y_offset += 30

    # Separator
    pygame.draw.line(screen, (100,100,100), (WIDTH - SIDEBAR_WIDTH + 10, y_offset + 10), (WIDTH - 10, y_offset + 10), 1)
    y_offset += 30

    # Queue Visualization
    queue_label = font.render(f"Queue (FIFO): {len(tree.queue)}", True, (255, 255, 255))
    screen.blit(queue_label, (WIDTH - SIDEBAR_WIDTH + 20, y_offset))
    y_offset += 40

    # Draw Queue Items (limited to fit screen)
    # We draw them as blocks to look like a data structure
    queue_x = WIDTH - SIDEBAR_WIDTH + 20
    for i, node in enumerate(tree.queue):
        if i > 12: # Limit display
            break
        
        # Color based on state
        q_color = COLOR_FRONTIER
        
        pygame.draw.rect(screen, q_color, (queue_x, y_offset, 40, 30))
        pygame.draw.rect(screen, (0,0,0), (queue_x, y_offset, 40, 30), 1)
        
        id_text = small_font.render(str(node.id), True, (0,0,0))
        text_rect = id_text.get_rect(center=(queue_x + 20, y_offset + 15))
        screen.blit(id_text, text_rect)
        
        queue_x += 45
        if queue_x > WIDTH - 60: # Wrap around
            queue_x = WIDTH - SIDEBAR_WIDTH + 20
            y_offset += 35

    y_offset = max(y_offset + 50, 450)
    
    # Message / Status
    msg_font = pygame.font.SysFont('arial', 20)
    
    # Split message into lines if too long
    words = tree.message.split(' ')
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > 25:
            lines.append(' '.join(current_line[:-1]))
            current_line = [word]
    lines.append(' '.join(current_line))

    pygame.draw.rect(screen, (20, 20, 20), (WIDTH - SIDEBAR_WIDTH + 10, y_offset, SIDEBAR_WIDTH - 20, 100))
    for i, line in enumerate(lines):
        msg = msg_font.render(line, True, COLOR_CURRENT)
        screen.blit(msg, (WIDTH - SIDEBAR_WIDTH + 20, y_offset + 10 + i * 25))

    # Controls
    controls = [
        "Left Click: Set Start",
        "Right Click: Set Goal",
        "SPACE: Step Forward",
        "R: Reset Search",
        "N: New Tree"
    ]
    y_offset += 120
    for c in controls:
        c_text = small_font.render(c, True, (150, 150, 150))
        screen.blit(c_text, (WIDTH - SIDEBAR_WIDTH + 20, y_offset))
        y_offset += 25


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("BFS Visualization - Interactive Learning")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 24, bold=True)

    tree = SearchTree()
    tree.generate_tree()

    running = True
    while running:
        # Event Handling
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
                    else:
                        tree.message = "Err: Select Start and Goal first!"
                elif event.key == pygame.K_r:
                    tree.reset_search()
                elif event.key == pygame.K_n:
                    tree.generate_tree()
                    tree.start_node = None
                    tree.goal_node = None
                    tree.reset_search()

        # Drawing
        screen.fill(BG_COLOR)
        
        # Draw Edges first (so they are behind nodes)
        for node in tree.nodes:
            node.draw(screen, font)
            
        # Draw Nodes
        for node in tree.nodes:
            node.draw_node_body(screen, font)

        draw_sidebar(screen, font, tree)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()