#!/bin/bash

# 检查文件是否存在
if [ ! -f "all_id_vector.scp" ]; then
    echo "错误: all_id_vector.scp 文件不存在"
    exit 1
fi

# 处理文件内容
while IFS= read -r line; do
    # 从路径中提取目录名（100）
    dir_name=$(basename "$(dirname "$line")")
    
    # 输出格式: 目录名 文件路径
    echo "$dir_name $line" >> spk2utt_id_vector.scp
done < "all_id_vector.scp"