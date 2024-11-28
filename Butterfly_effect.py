import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from scipy.integrate import odeint

# Lorenz方程
def lorenz(w, t, p, r, b): 
    x, y, z = w
    return np.array([p*(y-x), x*(r-z)-y, x*y-b*z]) 

# 設置參數
p, r, b = 10.0, 28.0, 3.0
t = np.arange(0, 20.0, 0.01)

# 設置隨機種子以確保可重複性
np.random.seed(42)

# 創建多個隨機的初始條件
num_trajectories = 5
base_point = np.array([1.0, 1.0, 10.0])  # 基準點
noise_scale = 0.1  # 隨機擾動的幅度

tracks = []
initial_conditions = []

for _ in range(num_trajectories):
    random_noise = np.random.normal(0, noise_scale, size=3)
    initial_condition = base_point + random_noise
    initial_conditions.append(initial_condition)
    
    track = odeint(lorenz, initial_condition, t, args=(p, r, b))
    tracks.append(track)

# 創建圖形
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d', position=[0.1, 0.1, 0.7, 0.8])

# 設置坐標軸
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_xlim3d([-20.0, 20.0])
ax.set_ylim3d([-25.0, 25.0])
ax.set_zlim3d([0.0, 50.0])
ax.set_title('Butterfly Effect in Lorenz System\nRandom initial conditions with σ=0.1')

# 創建每個軌跡的小球和線
colors = plt.cm.rainbow(np.linspace(0, 1, num_trajectories))
balls = []
lines = []

for color, init_cond in zip(colors, initial_conditions):
    ball, = ax.plot([], [], [], linestyle='None', marker='o',
                   markersize=8, markeredgecolor=color,
                   color='white', markeredgewidth=2)
    line, = ax.plot([], [], [], color=color, alpha=0.8, linewidth=1)
    balls.append(ball)
    lines.append(line)
    
    # 在圖例中顯示初始條件
    ax.text2D(1.15, 0.90 - len(balls)*0.05, 
              f'Init {len(balls)+1}: ({init_cond[0]:.2f}, {init_cond[1]:.2f}, {init_cond[2]:.2f})',
              transform=ax.transAxes, color=color, size=8)

# 添加時間顯示
time_box = dict(boxstyle='round,pad=0.5', fc='yellow', ec='k', alpha=0.7)
sim_time_text = ax.text2D(0.02, 0.95, '', transform=ax.transAxes, 
                         bbox=time_box, fontsize=10)
real_time_text = ax.text2D(0.02, 0.90, '', transform=ax.transAxes,
                          color='gray', fontsize=8)
progress_text = ax.text2D(0.02, 0.85, '', transform=ax.transAxes,
                         color='gray', fontsize=8)

def init():
    for ball, line in zip(balls, lines):
        ball.set_data([], [])
        ball.set_3d_properties([])
        line.set_data([], [])
        line.set_3d_properties([])
    sim_time_text.set_text('')
    real_time_text.set_text('')
    progress_text.set_text('')
    return balls + lines + [sim_time_text, real_time_text, progress_text]

def animate(frame):
    # 更新每個軌跡
    for ball, line, track in zip(balls, lines, tracks):
        # 更新球的位置
        x, y, z = track[frame, 0], track[frame, 1], track[frame, 2]
        ball.set_data([x], [y])
        ball.set_3d_properties([z])
        
        # 更新軌跡線
        line.set_data(track[:frame+1, 0], track[:frame+1, 1])
        line.set_3d_properties(track[:frame+1, 2])
    
    # 更新時間顯示
    sim_time_text.set_text(f'Simulation Time: {t[frame]:.2f}s')
    real_time_text.set_text(f'Frame: {frame}/{len(t)-1}')
    progress = (frame / (len(t)-1)) * 100
    progress_text.set_text(f'Progress: {progress:.1f}%')
    
    return balls + lines + [sim_time_text, real_time_text, progress_text]

# 創建動畫
anim = animation.FuncAnimation(fig, animate,
                             init_func=init,
                             frames=len(t),
                             interval=20,
                             blit=True)

# 添加說明文字
plt.figtext(0.02, 0.02, 'Trajectories with random initial conditions\n' +
            f'Base point: ({base_point[0]}, {base_point[1]}, {base_point[2]})\n' +
            f'Random noise: N(0, {noise_scale})', 
            fontsize=8, color='gray')

plt.show()