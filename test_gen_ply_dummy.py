import struct
import random
import math
import csv
import os

def create_auto_scaled_ply(csv_filename, output_ply="auto_guide.ply", num_points=10000):
    if not os.path.exists(csv_filename):
        print(f"Error: {csv_filename} が見つかりません。")
        return

    # 1. CSVからカメラ座標を読み込む
    cam_x, cam_y, cam_z = [], [], []
    with open(csv_filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cam_x.append(float(row['x']))
            cam_y.append(float(row['y']))
            cam_z.append(float(row['alt']))

    # 2. カメラの平均中心を被写体の中心(cx, cy, cz)と仮定
    # (注: もし被写体が原点固定ならここを 0, 0, 0.875 に書き換えてもOK)
    cx = sum(cam_x) / len(cam_x)
    cy = sum(cam_y) / len(cam_y)
    cz = sum(cam_z) / len(cam_z)

    # 3. 最適な半径(radius)の計算
    # 各カメラから中心までの距離の平均を出し、その50%程度を「被写体サイズ」とする
    distances = [math.sqrt((x-cx)**2 + (y-cy)**2 + (z-cz)**2) for x, y, z in zip(cam_x, cam_y, cam_z)]
    avg_dist = sum(distances) / len(distances)
    
    # 経験則：カメラまでの距離の約一半（0.5倍）が、被写体を囲むのに程よいサイズ
    auto_radius = avg_dist * 0.5 

    print(f"Calculated Center: ({cx:.3f}, {cy:.3f}, {cz:.3f})")
    print(f"Calculated Radius: {auto_radius:.3f}")

    # 4. PLY作成 (黄金パターンの「白・均一・RC偽装」)
    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        "comment Created in RealityCapture\n"
        f"element vertex {num_points}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar red\n"
        "property uchar green\n"
        "property uchar blue\n"
        "end_header\n"
    )

    with open(output_ply, 'wb') as f:
        f.write(header.encode('ascii'))
        for _ in range(num_points):
            phi = random.uniform(0, 2 * math.pi)
            costheta = random.uniform(-1, 1)
            u = random.uniform(0, 1)
            theta = math.acos(costheta)
            r = auto_radius * (u ** (1/3))
            
            x = cx + r * math.sin(theta) * math.cos(phi)
            y = cy + r * math.sin(theta) * math.sin(phi)
            z = cz + r * math.cos(theta)
            
            f.write(struct.pack('<fffBBB', x, y, z, 255, 255, 255))

    print(f"Success: {output_ply} created.")

# 実行（CSVのファイル名を指定してください）
create_auto_scaled_ply("camera_data.csv")