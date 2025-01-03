#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bpy
import math
import os
import shutil
import json

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
    target_y = radius * math.cos(math.radians(target_tilt_angle))
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
    math.radians(tilt_deg), 0, 
    target_x = math.radians(tilt_deg)
    target_y = 0
    target_z = math.radians(pan_deg)
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

if __name__ == '__main__':

    # シーンの設定

    # 画像のレンダリング設定
    bpy.context.scene.render.image_settings.file_format = 'PNG'

    # パラメータの設定
    CENTER_POSITION = (0, 0, 1.7)       # 被写体の中心位置（90度の時）
    RADIUS = 3                          # カメラが被写体から離れる距離
    FOCAL_LENGTH = 24                   # カメラの焦点距離
    ANGLE_INTERVAL = 10                 # 角度間隔（度単位）
    TILTS = [60, 90]                    # tiltの傾きの設定リスト（60度と90度）

    # ファイルの保存先のディレクトリを取得
    script_directory = os.path.dirname(bpy.data.filepath)

    # 画像の保存先のディレクトリを作成
    tmp_directory = os.path.join(script_directory, "generated_images")
    if os.path.exists(tmp_directory):
        shutil.rmtree(tmp_directory)  # ディレクトリを削除して空にする
    os.makedirs(tmp_directory)

    # JSONファイルの保存先
    json_file_path = os.path.join(tmp_directory, "camera_data.json")
    camera_data = []

    # レンダリングの実行
    for tilt_deg in TILTS:

        # tiltの傾きを設定
        for pan_deg in range(0, 360, ANGLE_INTERVAL):

            # 新しいカメラを作成
            camera = create_new_camera(camera_name=f"Camera_tilt_{tilt_deg:03d}_pan_{pan_deg:03d}")

            # カメラの位置を更新
            camera.location = calc_camera_location(CENTER_POSITION, RADIUS, pan_deg, tilt_deg)

            # カメラを常に中心（被写体）に向けるように回転
            camera.rotation_euler = calc_camera_rotation_euler(CENTER_POSITION, RADIUS, pan_deg, tilt_deg)

            # カメラの焦点距離を設定
            camera.data.lens = FOCAL_LENGTH

            # 新しく作成したカメラをアクティブに設定
            bpy.context.scene.camera = camera

            # 出力ファイル名を設定
            filename = f"{tmp_directory}/tilt_{tilt_deg:03d}_pan_{pan_deg:03d}.png"
            bpy.context.scene.render.filepath = filename

            # レンダリング実行
            bpy.ops.render.render(write_still=True)

            # カメラの位置と回転情報を辞書に格納
            camera_info = {
                "filename": filename,
                "tilt_angle": tilt_deg,
                "pan_angle": pan_deg,
                "center_position": {
                    "x": CENTER_POSITION[0],
                    "y": CENTER_POSITION[1],
                    "z": CENTER_POSITION[2]
                },
                "radius": RADIUS,
                "camera_location": {
                    "x": camera.location.x,
                    "y": camera.location.y,
                    "z": camera.location.z
                },
                "camera_rotation": {
                    "x": camera.rotation_euler.x,
                    "y": camera.rotation_euler.y,
                    "z": camera.rotation_euler.z
                },
                "camera_rotation_deg": {
                    "x": math.degrees(camera.rotation_euler.x),
                    "y": math.degrees(camera.rotation_euler.y),
                    "z": math.degrees(camera.rotation_euler.z)
                },
                "focal_length": {
                    "focal_length": camera.data.lens
                }
            }
            camera_data.append(camera_info)

            # デバッグ情報を表示
            print(f"Rendered: {filename}")
            print(f"Camera Position: {camera.location}")
            print(f"Camera Rotation: {camera.rotation_euler}")

            # # 新しく作成したカメラを削除してメモリを解放
            # bpy.data.objects.remove(camera, do_unlink=True)

    # カメラの位置と回転情報をJSONファイルに保存
    with open(json_file_path, 'w') as json_file:
        json.dump(camera_data, json_file, indent=4)

    print(f"Camera data saved to {json_file_path}")