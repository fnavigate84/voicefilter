import sys
from collections import defaultdict
import random
import numpy as np

def count_speakers(file_paths, spk_pos):
    unique_speakers = set()
    speaker_files = defaultdict(list)
    all_paths = set()
    duplicate_paths = []
    
    for file_path in file_paths:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # 检查文件路径是否重复
                if line in all_paths:
                    duplicate_paths.append(line)
                else:
                    all_paths.add(line)
                
                # 提取路径中的说话人ID
                parts = line.split('/')
                if len(parts) < spk_pos:
                    print(f"警告：忽略无效路径 {line}")
                    continue
                
                speaker_id = parts[-spk_pos]
                unique_speakers.add(speaker_id)
                speaker_files[speaker_id].append(line)
    
    return unique_speakers, speaker_files, duplicate_paths

def merge_speaker_stats(stats_list):
    """
    合并多个数据集的说话人统计结果
    
    Args:
        stats_list: 包含多个(unique_speakers, speaker_files, duplicate_paths)元组的列表
    
    Returns:
        合并后的(unique_speakers, speaker_files, duplicate_paths)
    """
    merged_unique = set()
    merged_speaker_files = defaultdict(list)
    merged_duplicate_paths = []
    
    for unique_speakers, speaker_files, duplicate_paths in stats_list:
        # 合并唯一说话人集合
        merged_unique |= unique_speakers
        
        # 合并说话人文件映射
        for speaker, files in speaker_files.items():
            merged_speaker_files[speaker].extend(files)
        
        # 合并重复路径列表
        merged_duplicate_paths.extend(duplicate_paths)
    
    return merged_unique, merged_speaker_files, merged_duplicate_paths

def write_spk2utt(speaker_files, output_file):
    """
    将说话人-音频文件映射写入spk2utt文件
    
    格式:
    speaker_id1 file_path1
    speaker_id1 file_path2
    speaker_id2 file_path3
    ...
    """
    with open(output_file, 'w') as f:
        # 先按说话人排序
        sorted_speakers = sorted(speaker_files.keys())
        for speaker in sorted_speakers:
            # 对每个说话人的文件路径排序
            sorted_files = sorted(speaker_files[speaker])
            for file_path in sorted_files:
                f.write(f"{speaker} {file_path}\n")
    
    print(f"已写入 {len(speaker_files)} 个说话人到 {output_file}")

if __name__ == "__main__":
    
    scp_file = '/home/mike/datasets/aishell3.scp'
    unique_speakers_aishell, speaker_files_aishell, duplicate_paths_aishell = count_speakers([scp_file], 3)
    scp_file = '/home/mike/datasets/slr33_aishell.scp'
    unique_speakers_slr_aishell, speaker_files_slr_aishell, duplicate_paths_slr_aishell = count_speakers([scp_file], 2)
    scp_file = '/home/mike/datasets/3d-speaker-no-reverb.scp'
    unique_speakers_3d, speaker_files_3d, duplicate_paths_3d = count_speakers([scp_file], 2)
    scp_file = '/home/mike/datasets/train-clean-100.scp'
    unique_speakers_100, speaker_files_100, duplicate_paths_100 = count_speakers([scp_file], 3)
    scp_file = '/home/mike/datasets/train-clean-360.scp'
    unique_speakers_360, speaker_files_360, duplicate_paths_360 = count_speakers([scp_file], 3)
    
    # 合并所有数据集的统计结果
    merged_unique, merged_speaker_files, merged_duplicate_paths = merge_speaker_stats([
        (unique_speakers_aishell, speaker_files_aishell, duplicate_paths_aishell),
        (unique_speakers_slr_aishell, speaker_files_slr_aishell, duplicate_paths_slr_aishell),
        (unique_speakers_3d, speaker_files_3d, duplicate_paths_3d),
        (unique_speakers_100, speaker_files_100, duplicate_paths_100),
        (unique_speakers_360, speaker_files_360, duplicate_paths_360)
    ])
    
    # 统计结果
    print(f"发现 {len(merged_unique)} 个不同的说话人")
    print("\n说话人列表:", ", ".join(sorted(merged_unique)))
    # 添加额外的重复检查
    merged_unique_list = list(merged_unique)
    if len(merged_unique_list) == len(set(merged_unique_list)):
        print("\n验证通过：merged_unique中没有重复的说话人ID")
    else:
        print("\n警告：发现重复的说话人ID")
        # 找出重复的ID
        seen = set()
        duplicates = set()
        for spk_id in merged_unique_list:
            if spk_id in seen:
                duplicates.add(spk_id)
            else:
                seen.add(spk_id)
        print(f"重复的说话人ID: {', '.join(sorted(duplicates))}")
    
    # 检查文件路径重复
    # if merged_duplicate_paths:
    #     print(f"\n警告：发现 {len(merged_duplicate_paths)} 个重复的文件路径:")
    #     for path in merged_duplicate_paths[:5]:  # 只显示前5个重复路径
    #         print(f"  - {path}")
    #     if len(merged_duplicate_paths) > 5:
    #         print(f"  ... 和另外 {len(merged_duplicate_paths)-5} 个重复路径")
    # else:
    #     print("\n所有文件路径均唯一")
    
    
    write_spk2utt(merged_speaker_files, 'merged_near_spk2utt.scp')
    
    # 检查说话人分布情况
    # speaker_counts = {spkr: len(files) for spkr, files in merged_speaker_files.items()}
    # min_count = min(speaker_counts.values())
    # max_count = max(speaker_counts.values())
    
    # 打乱merged_unique的顺序
    merged_unique_list = list(merged_unique)
    random.shuffle(merged_unique_list)
    
    # 定义划分比例（例如：70%训练，20%验证，10%测试）
    train_ratio = 0.75
    val_ratio = 0.2
    
    # 计算划分索引
    total = len(merged_unique_list)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    # 划分数据集
    train_speakers = merged_unique_list[:train_end]
    val_speakers = merged_unique_list[train_end:val_end]
    test_speakers = merged_unique_list[val_end:]
    
    # 函数：根据说话人ID集合提取对应的文件路径
    def get_file_paths(speaker_ids):
        file_paths = []
        for speaker_id in speaker_ids:
            if speaker_id in merged_speaker_files:
                file_paths.extend(merged_speaker_files[speaker_id])
        return file_paths
    
    # 获取各数据集的文件路径
    train_files = get_file_paths(train_speakers)
    val_files = get_file_paths(val_speakers)
    test_files = get_file_paths(test_speakers)
    
    # 定义函数：将文件路径写入scp文件
    def write_scp(file_paths, output_file):
        with open(output_file, 'w') as f:
            for file_path in file_paths:
                f.write(f"{file_path}\n")
    
    # 生成scp文件
    write_scp(train_files, 'train.scp')
    write_scp(val_files, 'validate.scp')
    write_scp(test_files, 'test.scp')
    
    print(f"数据集划分完成：")
    print(f"- 训练集：{len(train_files)}个文件")
    print(f"- 验证集：{len(val_files)}个文件")
    print(f"- 测试集：{len(test_files)}个文件")