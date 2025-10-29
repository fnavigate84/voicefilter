import os
import glob
import tqdm
import torch
import random
import librosa
import argparse
import numpy as np
from multiprocessing import Pool, cpu_count

from utils.audio import Audio
from utils.hparams import HParam
import soundfile as sf
from model.embedder import SpeechEmbedder
from utils.audio import Audio
import re
import concurrent.futures
from functools import partial

def read_spk2utt_file(file_path):
    """读取spk2utt文件并组织为字典"""
    spk_data = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(' ', 1)  # 只分割一次，保留路径中的空格
            if len(parts) < 2:
                print(f"警告: 忽略无效行: {line}")
                continue
            
            spk_id, wav_path = parts
            if spk_id not in spk_data:
                spk_data[spk_id] = []
            spk_data[spk_id].append(wav_path)
    
    print(f"从 {file_path} 读取了 {len(spk_data)} 个说话人的 {sum(len(v) for v in spk_data.values())} 条记录")
    return spk_data
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, required=True,
                        help="yaml file for configuration")
    parser.add_argument('-d', '--libri_dir', type=str, default=None,
                        help="Directory of LibriSpeech dataset, containing folders of train-clean-100, train-clean-360, dev-clean.")
    parser.add_argument('-o', '--out_dir', type=str, required=True,
                        help="Directory of output training triplet")
    parser.add_argument('-p', '--process_num', type=int, default=None,
                        help='number of processes to run. default: cpu_count')
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    hp = HParam(args.config)

    cpu_num = args.process_num
    
    audio = Audio(hp)

    # load spk2utt file
    args.spk2utt_file = 'merged_near_spk2utt.scp'
    spk_data = read_spk2utt_file(args.spk2utt_file)
    
    # load embedder
    args.embedder_path = "d-vector-model/embedder.pt"
    embedder_pt = torch.load(args.embedder_path)
    embedder = SpeechEmbedder(hp).cuda()
    embedder.load_state_dict(embedder_pt)
    embedder.eval()
    
    def process_wav(wav, spk_id, embedder, args):
        # 先构建输出文件路径
        wav_name = os.path.basename(wav).split('.')[0]
        output_dir = os.path.join(args.out_dir, f'{spk_id}')
        output_path = os.path.join(output_dir, wav_name + '.pt')
        
        # 检查目标文件是否已存在，如果存在则跳过
        if os.path.exists(output_path):
            return
        
        # 文件不存在，执行声纹提取
        dvec_wav, _ = librosa.load(wav, sr=hp.audio.sample_rate)
        dvec_mel = audio.get_mel(dvec_wav)
        dvec_mel = torch.from_numpy(dvec_mel).float().to('cuda')
        spk_vector = embedder(dvec_mel).cpu()
        
        # 创建输出目录并保存声纹
        os.makedirs(output_dir, exist_ok=True)
        torch.save(spk_vector, output_path)

    for spk_id, wav_paths in tqdm.tqdm(spk_data.items()):
        print(f"Processing speaker {spk_id} with {len(wav_paths)} audio files")
        # 使用线程池并行处理当前说话人的所有音频文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 绑定固定参数，只传递wav文件路径作为变量参数
            process_func = partial(process_wav, spk_id=spk_id, embedder=embedder, args=args)
            executor.map(process_func, wav_paths)