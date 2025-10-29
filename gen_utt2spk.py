import os
import argparse

def create_utt2spk_from_spk2utt(input_file, output_file):
    """
    从spk2utt文件创建utt2spk文件
    
    参数:
        input_file: spk2utt文件路径
        output_file: 输出的utt2spk文件路径
    """
    
    # 统计处理的行数
    total_lines = 0
    total_utterances = 0
    
    # 打开输入和输出文件
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
                
            total_lines += 1
            
            # 分割行: 说话人ID + 文件路径列表
            parts = line.split()
            if len(parts) < 2:
                print(f"警告: 忽略无效行: {line}")
                continue
                
            spk_id = parts[0]
            file_paths = parts[1:]
            
            for file_path in file_paths:
                # 获取文件名（不含扩展名）
                file_name = os.path.basename(file_path)
                utt_id = os.path.splitext(file_name)[0]
                
                # 写入行: utt_id spk_id
                f_out.write(f"{utt_id} {spk_id}\n")
                total_utterances += 1
    
    print(f"处理完成: 读取 {total_lines} 行，生成 {total_utterances} 条utt2spk记录")
    print(f"已创建utt2spk文件: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从spk2utt文件创建utt2spk文件")
    parser.add_argument("--input_file", type=str, required=True,
                        help="输入的spk2utt文件路径")
    parser.add_argument("--output_file", type=str, required=True,
                        help="输出的utt2spk文件路径")
    
    args = parser.parse_args()
    
    create_utt2spk_from_spk2utt(args.input_file, args.output_file)