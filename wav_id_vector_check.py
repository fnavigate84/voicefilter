import os
import argparse

def find_missing_files(audio_scp_file, vector_scp_file, output_file=None):
    """
    找出在vector_scp_file中没有对应.pt文件的音频文件
    
    参数:
        audio_scp_file: 音频文件列表 (merged_near_spk2utt.scp)
        vector_scp_file: 声纹向量文件列表 (spk2utt_near_id_vector.scp)
        output_file: 输出结果文件路径
    """
    # 步骤1: 从音频文件中提取文件名（不含扩展名）
    audio_files = set()
    with open(audio_scp_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            # 获取最后一个部分（文件路径）
            wav_path = parts[-1]
            # 提取文件名（不含扩展名）
            file_name = os.path.basename(wav_path)
            audio_id = os.path.splitext(file_name)[0]
            audio_files.add(audio_id)
    
    print(f"从 {audio_scp_file} 读取了 {len(audio_files)} 个音频文件")
    
    # 步骤2: 从向量文件中提取文件名（不含扩展名）
    vector_files = set()
    with open(vector_scp_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            # 获取最后一个部分（文件路径）
            pt_path = parts[-1]
            # 提取文件名（不含扩展名）
            file_name = os.path.basename(pt_path)
            vector_id = os.path.splitext(file_name)[0]
            vector_files.add(vector_id)
    
    print(f"从 {vector_scp_file} 读取了 {len(vector_files)} 个向量文件")
    
    # 步骤3: 找出缺失的文件
    missing_files = audio_files - vector_files
    print(f"发现 {len(missing_files)} 个音频文件没有对应的向量文件")
    
    # 步骤4: 输出结果
    if output_file:
        with open(output_file, 'w') as f_out:
            for file_id in sorted(missing_files):
                f_out.write(file_id + '\n')
        print(f"结果已保存到 {output_file}")
    else:
        print("\n缺失的文件列表:")
        for i, file_id in enumerate(sorted(missing_files)[:50]):  # 最多显示50个
            print(f"  {i+1}. {file_id}")
        if len(missing_files) > 50:
            print(f"  ... 和另外 {len(missing_files)-50} 个文件")
    
    return missing_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="检查缺失的向量文件")
    parser.add_argument("--audio_scp", type=str, required=True,
                        help="音频文件列表 (merged_near_spk2utt.scp)")
    parser.add_argument("--vector_scp", type=str, required=True,
                        help="向量文件列表 (spk2utt_near_id_vector.scp)")
    parser.add_argument("--output", type=str, default=None,
                        help="输出结果文件路径")
    
    args = parser.parse_args()
    
    missing_files = find_missing_files(args.audio_scp, args.vector_scp, args.output)