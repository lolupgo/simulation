import pygame
import random

# --- Constants ---
WIDTH, HEIGHT = 1200, 800
SIDEBAR_WIDTH = 350
NODE_RADIUS = 25
FPS = 60

# Colors
BG_COLOR = (30, 30, 30)
SIDEBAR_BG = (45, 45, 45)
TEXT_COLOR = (220, 220, 220)
EDGE_COLOR = (80, 80, 80)

COLOR_DEFAULT = (100, 100, 100) # Grey
COLOR_CURRENT = (0, 255, 255)   # Cyan (The climber)
COLOR_NEIGHBOR = (255, 200, 0)  # Yellow (Candidate to move to)
COLOR_BETTER = (0, 200, 0)      # Green (Better neighbor found)
COLOR_WORSE = (200, 0, 0)       # Red (Worse neighbor rejected)
COLOR_PEAK = (255, 0, 255)      # Magenta (Local Max reached)

# --- Classes ---

class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.neighbors = []
        
        # The "Value" or "Height" of this node (0 to 100)
        # In Hill Climbing, we want to maximize this.
        self.score = 0 
        
        self.state = 'default' # default, current, neighbor, better, worse, peak

    def draw_edges(self, screen):
        for neighbor in self.neighbors:
            pygame.draw.line(screen, EDGE_COLOR, (self.x, self.y), (neighbor.x, neighbor.y), 2)

    def draw_body(self, screen, font, small_font):
        # Base color
        color = COLOR_DEFAULT
        if self.state == 'current': color = COLOR_CURRENT
        elif self.state == 'neighbor': color = COLOR_NEIGHBOR
        elif self.state == 'better': color = COLOR_BETTER
        elif self.state == 'worse': color = COLOR_WORSE
        elif self.state == 'peak': color = COLOR_PEAK

        # Size can slightly represent score for visual cue
        radius = NODE_RADIUS + (self.score / 20) 

        pygame.draw.circle(screen, color, (self.x, self.y), radius)
        pygame.draw.circle(screen, (255, 255, 255), (self.x, self.y), radius, 2)

        # ID
        text = font.render(str(self.id), True, (255,255,255) if color != COLOR_CURRENT else (0,0,0))
        screen.blit(text, text.get_rect(center=(self.x, self.y - 10)))
        
        # Score (Elevation)
        score_txt = small_font.render(f"H: {self.score}", True, (255, 255, 0))
        screen.blit(score_txt, score_txt.get_rect(center=(self.x, self.y + 15)))

class HillClimbingSim:
    def __init__(self):
        self.nodes = []
        self.current_node = None
        self.message = "Click any node to Start Climbing."
        self.running = False
        self.completed = False
        self.best_neighbor = None
        
        # Step logic control
        self.step_stage = 0 
        # 0: Just landed on current
        # 1: Identify Neighbors
        # 2: Evaluate Neighbors (Compare Scores)
        # 3: Move or Stop

    def generate_landscape(self):
        self.nodes = []
        self.current_node = None
        self.running = False
        self.completed = False
        
        # Create a grid-like graph for better "landscape" feel
        rows, cols = 5, 6
        x_spacing = (WIDTH - SIDEBAR_WIDTH) // (cols + 1)
        y_spacing = HEIGHT // (rows + 1)
        
        count = 0
        grid = {} # Map (r,c) to node

        for r in range(rows):
            for c in range(cols):
                # Add some jitter to x, y so it looks organic
                jx = random.randint(-20, 20)
                jy = random.randint(-20, 20)
                node = Node(count, x_spacing * (c+1) + jx, y_spacing * (r+1) + jy)
                
                # Assign Random "Height" (Score)
                # Make center ones generally higher to create a "Hill" structure probability
                center_bonus = 30 - (abs(r - 2) * 10 + abs(c - 3) * 5)
                base_score = random.randint(10, 60)
                node.score = max(0, min(100, base_score + int(center_bonus)))
                
                self.nodes.append(node)
                grid[(r,c)] = node
                count += 1
        
        # Connect Neighbors (Grid adjacency + Diagonals)
        for r in range(rows):
            for c in range(cols):
                node = grid[(r,c)]
                # Look at 8 neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr==0 and dc==0: continue
                        nr, nc = r+dr, c+dc
                        if (nr, nc) in grid:
                            neighbor = grid[(nr,nc)]
                            # Add connection (undirected)
                            if neighbor not in node.neighbors:
                                node.neighbors.append(neighbor)
                                neighbor.neighbors.append(node)

    def handle_click(self, pos):
        if self.running: return # Can't click while running
        x, y = pos
        for node in self.nodes:
            # Distance check
            if ((x - node.x)**2 + (y - node.y)**2)**0.5 < NODE_RADIUS + 5:
                # Reset previous
                for n in self.nodes: n.state = 'default'
                
                self.current_node = node
                self.current_node.state = 'current'
                self.message = f"Start set at Node {node.id} (Height: {node.score}). Press SPACE."
                self.running = True
                self.completed = False
                self.step_stage = 1
                return

    def step(self):
        if not self.running or self.completed or not self.current_node:
            return

        # --- Stage 1: Identify Neighbors ---
        if self.step_stage == 1:
            self.message = "Checking neighbors..."
            # Reset colors
            for n in self.nodes:
                if n != self.current_node: n.state = 'default'
            
            # Highlight neighbors
            neighbors = self.current_node.neighbors
            if not neighbors:
                self.message = "No neighbors! Stuck."
                self.current_node.state = 'peak'
                self.completed = True
                return

            for n in neighbors:
                n.state = 'neighbor'
            
            self.message = f"Found {len(neighbors)} neighbors. Press SPACE to Evaluate."
            self.step_stage = 2

        # --- Stage 2: Evaluate (Find Highest) ---
        elif self.step_stage == 2:
            neighbors = self.current_node.neighbors
            current_score = self.current_node.score
            
            # Find the best neighbor
            best = None
            highest_score = -1

            for n in neighbors:
                if n.score > current_score:
                    n.state = 'better'
                    if n.score > highest_score:
                        highest_score = n.score
                        best = n
                else:
                    n.state = 'worse' # Red if lower or equal (flat plateau is bad for simple hill climbing)
            
            self.best_neighbor = best
            
            if best:
                self.message = f"Best Move: Node {best.id} (H: {best.score}). Higher than {current_score}."
            else:
                self.message = "No neighbors are higher. We are at a Peak."
            
            self.step_stage = 3

        # --- Stage 3: Move or Stop ---
        elif self.step_stage == 3:
            if self.best_neighbor:
                # Move climber
                self.current_node.state = 'default'
                self.current_node = self.best_neighbor
                self.current_node.state = 'current'
                
                # Reset others
                for n in self.nodes:
                    if n != self.current_node: n.state = 'default'
                
                self.message = f"Moved to Node {self.current_node.id}. Press SPACE to continue."
                self.step_stage = 1 # Back to finding neighbors
            else:
                # Stop - Local Maxima
                self.current_node.state = 'peak'
                self.completed = True
                
                # Check if it is actually the global max
                global_max = max(node.score for node in self.nodes)
                if self.current_node.score == global_max:
                    self.message = "Global Maximum Reached! (Highest Point)"
                else:
                    self.message = f"Stuck at Local Max (H:{self.current_node.score}). Global Max is {global_max}."


# --- UI ---
def draw_sidebar(screen, font, small_font, sim):
    rect = pygame.Rect(WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(screen, SIDEBAR_BG, rect)
    pygame.draw.line(screen, (100,100,100), (WIDTH - SIDEBAR_WIDTH, 0), (WIDTH - SIDEBAR_WIDTH, HEIGHT), 2)

    title = font.render("Hill Climbing Search", True, (255, 255, 255))
    screen.blit(title, (WIDTH - SIDEBAR_WIDTH + 20, 20))
    
    # Legend
    y_off = 80
    legend_data = [
        ("Current Position", COLOR_CURRENT),
        ("Higher Neighbor (Good)", COLOR_BETTER),
        ("Lower/Equal (Bad)", COLOR_WORSE),
        ("Local Maximum (Stuck)", COLOR_PEAK)
    ]
    for txt, col in legend_data:
        pygame.draw.circle(screen, col, (WIDTH - SIDEBAR_WIDTH + 30, y_off+10), 8)
        screen.blit(small_font.render(txt, True, TEXT_COLOR), (WIDTH - SIDEBAR_WIDTH + 50, y_off))
        y_off += 30

    y_off += 30
    
    # Current Stats
    if sim.current_node:
        txt_curr = font.render(f"Current Height: {sim.current_node.score}", True, COLOR_CURRENT)
        screen.blit(txt_curr, (WIDTH - SIDEBAR_WIDTH + 20, y_off))
    
    # Explanation Text
    y_off += 50
    explanation = [
        "Algorithm Logic:",
        "1. Look at immediate neighbors.",
        "2. If a neighbor is HIGHER,",
        "   move to the highest one.",
        "3. If all neighbors are LOWER,",
        "   STOP.",
        "",
        "Note: This does not backtrack!",
        "It can get stuck on small hills."
    ]
    
    for line in explanation:
        l_surf = small_font.render(line, True, (180, 180, 180))
        screen.blit(l_surf, (WIDTH - SIDEBAR_WIDTH + 20, y_off))
        y_off += 25

    # Status Bar
    status_y = HEIGHT - 100
    pygame.draw.rect(screen, (20,20,20), (WIDTH-SIDEBAR_WIDTH+10, status_y, SIDEBAR_WIDTH-20, 80))
    
    # Word wrap message
    words = sim.message.split(' ')
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        if len(' '.join(curr)) > 30:
            lines.append(' '.join(curr[:-1]))
            curr = [w]
    lines.append(' '.join(curr))
    
    for i, ln in enumerate(lines):
        msg_surf = small_font.render(ln, True, COLOR_CURRENT)
        screen.blit(msg_surf, (WIDTH-SIDEBAR_WIDTH+20, status_y+10 + i*20))
        
    controls = small_font.render("Space: Step | R: Restart | N: New Map", True, (150,150,150))
    screen.blit(controls, (WIDTH-SIDEBAR_WIDTH+20, HEIGHT-30))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Hill Climbing Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 24, bold=True)
    small_font = pygame.font.SysFont('arial', 18)

    sim = HillClimbingSim()
    sim.generate_landscape()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                sim.handle_click(pygame.mouse.get_pos())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: sim.step()
                elif event.key == pygame.K_r: 
                    # Reset climber but keep map
                    sim.running = False
                    sim.completed = False
                    sim.current_node = None
                    sim.message = "Click any node to Start."
                    for n in sim.nodes: n.state = 'default'
                elif event.key == pygame.K_n:
                    sim.generate_landscape()

        screen.fill(BG_COLOR)
        
        # Draw edges first
        for node in sim.nodes: node.draw_edges(screen)
        # Draw nodes
        for node in sim.nodes: node.draw_body(screen, font, small_font)
        
        draw_sidebar(screen, font, small_font, sim)
        
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__": main()