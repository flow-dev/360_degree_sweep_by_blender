#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bpy
import math
import os
import shutil
import json
import csv
import struct
import random

# --- 追加機能：自動スケーリングされた白い点群の生成 ---
def create_auto_white_ply(camera_locations, output_ply, num_points=10000):
    """
    カメラの座標リストから中心と半径を割り出し、白いPLYを作成する
    """
    if not camera_locations:
        return

    # 1. 中心座標の計算
    cx = sum(p[0] for p in camera_locations) / len(camera_locations)
    cy = sum(p[1] for p in camera_locations) / len(camera_locations)
    cz = sum(p[2] for p in camera_locations) / len(camera_locations)

    # 2. 半径の計算（カメラまでの平均距離の50%）
    distances = [math.sqrt((p[0]-cx)**2 + (p[1]-cy)**2 + (p[2]-cz)**2) for p in camera_locations]
    avg_dist = sum(distances) / len(distances)
    auto_radius = avg_dist * 0.5 

    print(f"Auto PLY - Center: ({cx:.3f}, {cy:.3f}, {cz:.3f}), Radius: {auto_radius:.3f}")

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
    print(f"Success: {output_ply} created with {num_points} points.")
    return

def calc_camera_location(center_position, radius, pan_angle, tilt_angle):
    """
    カメラの位置を計算する関数
    :param center_position: 被写体の中心位置
    :param radius: カメラが被写体から離れる距離
    :param pan_angle: カメラのパン角度（水平方向の角度）
    :param tilt_angle: カメラのチルト角度（垂直方向の角度）
    :return: カメラの位置（x, y, z）
    """
    target_tilt_angle = 90 - tilt_angle
    target_x = radius * math.sin(math.radians(pan_angle)) * math.cos(math.radians(target_tilt_angle)) + center_position[0]
    target_y = -1 * radius * math.cos(math.radians(target_tilt_angle)) * math.cos(math.radians(pan_angle))
    target_z = radius * math.sin(math.radians(target_tilt_angle)) + CENTER_POSITION[2]
    print(f"target_x: {target_x}, target_y: {target_y}, target_z: {target_z}")
    return (target_x, target_y, target_z)

def calc_camera_rotation_euler(center_position, radius, pan_angle, tilt_angle):
    """
    カメラの回転情報を計算する関数
    :param center_position: 被写体の中心位置
    :param radius: カメラが被写体から離れる距離
    :param pan_angle: カメラのパン角度（水平方向の角度）
    :param tilt_angle: カメラのチルト角度（垂直方向の角度）
    :return: カメラの回転情報（x, y, z）
    """
    target_x = math.radians(tilt_angle)
    target_y = 0
    target_z = math.radians(pan_angle)
    print(f"target_rotation_euler_x: {target_x}, target_rotation_euler_y: {target_y}, target_rotation_euler_z: {target_z}")
    return (target_x, target_y, target_z)

def create_new_camera(camera_name="Camera"):
    """
    新しいカメラを作成する関数
    :param camera_name: カメラの名前
    :return: 新しいカメラオブジェクト
    """
    bpy.ops.object.camera_add(location=(0, 0, 0))
    new_camera = bpy.context.object
    new_camera.name = camera_name
    return new_camera

def create_or_clear_collection(collection_name="CameraCollection"):
    # コレクションがすでに存在する場合、削除して空にする
    if collection_name in bpy.data.collections:
        existing_collection = bpy.data.collections[collection_name]
        # コレクション内のすべてのオブジェクトを削除
        for obj in list(existing_collection.objects):
            existing_collection.objects.unlink(obj)
        return existing_collection
    else:
        # 新しいコレクションを作成
        new_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(new_collection)
        return new_collection

if __name__ == '__main__':

    # シーンの設定

    # # 画像のレンダリング設定
    # bpy.context.scene.render.image_settings.file_format = 'PNG'
    
    # 画像形式をJPEGに設定し、品質を80に設定
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.image_settings.quality = 80

    # パラメータの設定
    CENTER_POSITION = (0, 0, 0.875)       # 被写体の中心位置（90度の時）
    RADIUS = 3                          # カメラが被写体から離れる距離
    FOCAL_LENGTH_ST = 70                # カメラの焦点距離（開始）
    FOCAL_LENGTH_ED = 70                # カメラの焦点距離（終了）
    FOCAL_LENGTH_INTERVAL = 1           # カメラの焦点距離の間隔
    PAN_ANGLE_INTERVAL = 10             # Pan角度間隔（度単位）
    TILT_ANGLE_INTERVAL = 10            # Tilt角度間隔（度単位）

    # ファイルの保存先のディレクトリを取得
    script_directory = os.path.dirname(bpy.data.filepath)

    # 画像の保存先のディレクトリを作成
    tmp_directory = os.path.join(script_directory, "generated_images3")
    if os.path.exists(tmp_directory):
        shutil.rmtree(tmp_directory)  # ディレクトリを削除して空にする
    os.makedirs(tmp_directory)

    # JSONファイルの保存先
    json_file_path = os.path.join(tmp_directory, "camera_data.json")
    csv_file_path = os.path.join(tmp_directory, "camera_data.csv")
    camera_data = []
    camera_locations = []  # カメラの位置を保存するリスト

    # 新しいコレクションを作成または既存のコレクションを空にしてアクティブに設定
    camera_collection = create_or_clear_collection("CameraCollection")
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[camera_collection.name]

    # カメラの数をカウント
    count = 0

    # レンダリングの実行
    for focal_length_val in range(FOCAL_LENGTH_ST, (FOCAL_LENGTH_ED + 1), FOCAL_LENGTH_INTERVAL):

        for tilt_deg in range(0, (180 + 1), TILT_ANGLE_INTERVAL):

            # tiltの傾きを設定
            for pan_deg in range(0, 360, PAN_ANGLE_INTERVAL): # 0度から360度まで
            # for pan_deg in list(range(270, 360, PAN_ANGLE_INTERVAL)) + list(range(0, (90 + 1), PAN_ANGLE_INTERVAL)):  # 0度から90度までと270度から360度まで

                # 新しいカメラを作成
                camera = create_new_camera(camera_name=f"Camera_{count:04d}_tilt_{tilt_deg:03d}_pan_{pan_deg:03d}_f{focal_length_val}")

                # カメラの位置を更新
                camera.location = calc_camera_location(CENTER_POSITION, RADIUS, pan_deg, tilt_deg)

                # カメラを常に中心（被写体）に向けるように回転
                camera.rotation_euler = calc_camera_rotation_euler(CENTER_POSITION, RADIUS, pan_deg, tilt_deg)

                # カメラの焦点距離を設定
                camera.data.lens = focal_length_val

                # カメラ座標をリストに保存
                camera_locations.append(camera.location)

                # 新しく作成したカメラをアクティブに設定
                bpy.context.scene.camera = camera

                # 出力ファイル名を設定
                # filename = f"{tmp_directory}/{count:04d}_tilt_{tilt_deg:03d}_pan_{pan_deg:03d}_f{focal_length_val}.png"
                filename = f"{tmp_directory}/{count:04d}_tilt_{tilt_deg:03d}_pan_{pan_deg:03d}_f{focal_length_val}.jpg"
                bpy.context.scene.render.filepath = filename

                # レンダリング実行
                bpy.ops.render.render(write_still=True)

                # カメラの位置と回転情報を辞書に格納
                camera_info = {
                    "id": count, # カメラのID
                    "filename": os.path.basename(filename), # レンダリング画像のファイル名
                    "tilt_angle": tilt_deg, # チルト角度
                    "pan_angle": pan_deg,  # パン角度
                    "center_position": { # 被写体の中心位置
                        "x": CENTER_POSITION[0],
                        "y": CENTER_POSITION[1],
                        "z": CENTER_POSITION[2]
                    },
                    "radius": RADIUS,
                    "camera_location": { # カメラの位置
                        "x": round(camera.location.x,6),
                        "y": round(camera.location.y,6),
                        "z": round(camera.location.z,6)
                    },
                    "camera_rotation": { # カメラの回転角度（ラジアン単位）
                        "x": round(camera.rotation_euler.x,6),
                        "y": round(camera.rotation_euler.y,6),
                        "z": round(camera.rotation_euler.z,6)
                    },
                    "camera_rotation_deg": { # カメラの回転角度（度単位）
                        "x": round(math.degrees(camera.rotation_euler.x),6),
                        "y": round(math.degrees(camera.rotation_euler.y),6),
                        "z": round(math.degrees(camera.rotation_euler.z),6)
                    },
                    "focal_length": { # カメラの焦点距離
                        "focal_length": camera.data.lens,
                        "focal_length_pixel": round(((bpy.context.scene.render.resolution_x / camera.data.sensor_width) * camera.data.lens) , 6),
                        "focal_length_36mm_equiv": round((camera.data.lens * (36.0 / camera.data.sensor_width)), 6) # RealityCapture仕様に合わせてsensor_with=36mm換算焦点距離を追加
                    },
                    "resolution": { # レンダリング画像の解像度
                        "width": bpy.context.scene.render.resolution_x,
                        "height": bpy.context.scene.render.resolution_y
                    },
                    "sensor": { # センサーサイズ
                        "width": camera.data.sensor_width,
                        "height": round((camera.data.sensor_width * (bpy.context.scene.render.resolution_y / bpy.context.scene.render.resolution_x)),6)
                    }
                }
                camera_data.append(camera_info)

                # デバッグ情報を表示
                print(f"Rendered: {os.path.basename(filename)}")
                print(f"Camera Position: {camera.location}")
                print(f"Camera Rotation: {camera.rotation_euler}")

                # # 新しく作成したカメラを削除してメモリを解放
                # bpy.data.objects.remove(camera, do_unlink=True)

                # カウンタを更新
                count += 1

    # カメラの位置と回転情報をJSONファイルに保存
    with open(json_file_path, 'w') as json_file:
        json.dump(camera_data, json_file, indent=4)

    # CSVファイルに書き込み
    with open(csv_file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # RealityCapture互換ヘッダー
        writer.writerow(['#name', 'x', 'y', 'alt', 'heading', 'pitch', 'roll', 'f', 'px', 'py', 'k1', 'k2', 'k3', 'k4', 't1', 't2'])
        
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        for item in data:
                writer.writerow([
                    os.path.basename(item['filename']),
                    item['camera_location']['x'],
                    item['camera_location']['y'],
                    item['camera_location']['z'],   # z を alt に入れる
                    -item['camera_rotation_deg']['z'], # heading (符号反転が必要な場合あり)
                    item['camera_rotation_deg']['x'],  # pitch
                    item['camera_rotation_deg']['y'],  # roll
                    item['focal_length']['focal_length_36mm_equiv'], # f　!RealityCapture仕様に合わせてsensor_with=36mm換算焦点距離を追加
                    0, 0, 0, 0, 0, 0, 0, 0 # その他レンズ歪みなどは0
                ])

    # 自動計算された3DGSガイド用PLYの書き出し
    ply_file_path = os.path.join(tmp_directory, "init_guide_points.ply")
    create_auto_white_ply(camera_locations, ply_file_path)

    print(f"Camera data saved to {json_file_path},{csv_file_path}")
    print("Done! CSV and PLY are ready for Postshot.")
    