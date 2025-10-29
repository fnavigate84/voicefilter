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

def extract_speaker_id_regex(file_path):
    """使用正则表达式提取说话人ID"""
    match = re.search(r'/(\d+)/', file_path)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"无法从路径 {file_path} 中提取说话人ID")
    
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
    os.makedirs(os.path.join(args.out_dir, 'train_id_vector'), exist_ok=True)
    os.makedirs(os.path.join(args.out_dir, 'test_id_vector'), exist_ok=True)

    hp = HParam(args.config)

    cpu_num = args.process_num
    
    audio = Audio(hp)

    args.libri_dir = "/home/mike/datasets"
    if args.libri_dir is None and args.voxceleb_dir is None:
        raise Exception("Please provide directory of data")

    if args.libri_dir is not None:
        train_folders = [x for x in glob.glob(os.path.join(args.libri_dir, 'train-clean-100', '*'))
                            if os.path.isdir(x)] + \
                        [x for x in glob.glob(os.path.join(args.libri_dir, 'train-clean-360', '*'))
                            if os.path.isdir(x)]
                        # we recommned to exclude train-other-500
                        # See https://github.com/mindslab-ai/voicefilter/issues/5#issuecomment-497746793
                        # + \
                        #[x for x in glob.glob(os.path.join(args.libri_dir, 'train-other-500', '*'))
                        #    if os.path.isdir(x)]
        test_folders = [x for x in glob.glob(os.path.join(args.libri_dir, 'dev-clean', '*'))]

    elif args.voxceleb_dir is not None:
        all_folders = [x for x in glob.glob(os.path.join(args.voxceleb_dir, '*'))
                            if os.path.isdir(x)]
        train_folders = all_folders[:-20]
        test_folders = all_folders[-20:]

    train_spk = [glob.glob(os.path.join(spk, '**', hp.form.input), recursive=True)
                    for spk in train_folders]
    train_spk = [x for x in train_spk if len(x) >= 2]

    test_spk = [glob.glob(os.path.join(spk, '**', hp.form.input), recursive=True)
                    for spk in test_folders]
    test_spk = [x for x in test_spk if len(x) >= 2]
    
    # load embedder
    args.embedder_path = "d-vector-model/embedder.pt"
    embedder_pt = torch.load(args.embedder_path)
    embedder = SpeechEmbedder(hp).cuda()
    embedder.load_state_dict(embedder_pt)
    embedder.eval()
    
    def process_wav(wav, spk_id, embedder, train, args):
        dvec_wav, _ = librosa.load(wav, sr=hp.audio.sample_rate)
        dvec_mel = audio.get_mel(dvec_wav)
        dvec_mel = torch.from_numpy(dvec_mel).float().to('cuda')
        spk_vector = embedder(dvec_mel).cpu()
        wav_name = os.path.basename(wav).split('.')[0]
        if train:
            output_dir = os.path.join(args.out_dir, f'train_id_vector/{spk_id}')
        else:
            output_dir = os.path.join(args.out_dir, f'test_id_vector/{spk_id}')
        os.makedirs(output_dir, exist_ok=True)
        torch.save(spk_vector, os.path.join(output_dir, wav_name + '.pt'))

    for spk in tqdm.tqdm(train_spk):
        spk_id = extract_speaker_id_regex(spk[0])
        print(f"Processing speaker {spk_id}")
        # 使用线程池并行处理当前说话人的所有音频文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 绑定固定参数，只传递wav文件路径作为变量参数
            process_func = partial(process_wav, spk_id=spk_id, embedder=embedder, train=True, args=args)
            executor.map(process_func, spk)

    for spk in tqdm.tqdm(test_spk):
        spk_id = extract_speaker_id_regex(spk[0])
        print(f"Processing speaker {spk_id}")
        # 使用线程池并行处理当前说话人的所有音频文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 绑定固定参数，只传递wav文件路径作为变量参数
            process_func = partial(process_wav, spk_id=spk_id, embedder=embedder, train=False, args=args)
            executor.map(process_func, spk)