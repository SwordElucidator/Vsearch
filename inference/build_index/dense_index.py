import argparse
import json
from tqdm import tqdm
import torch
from src.ir import Retriever

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--text_file', required=True, help='Path to the text file to be indexed.')
    parser.add_argument('-s', '--save_file', required=True, help='Path where the output .pt index file will be saved.')
    parser.add_argument('-c', '--checkpoint', default='vsearch/dpr-nq', type=str, help='Path to the model checkpoint.') 
    parser.add_argument('-bs', '--batch_size', default=256, type=int)
    parser.add_argument('-n', '--num_shard', default=1, type=int)
    parser.add_argument('-i', '--shard_id', default=0, type=int)
    parser.add_argument('-d', '--device', default="cuda", type=str)

    args = parser.parse_args()
    
    print(args)

    print(f"### Load Model: {args.checkpoint} ###")
    dpr = Retriever.from_pretrained(args.checkpoint)
    dpr = dpr.to(args.device)

    print(f"### Load Text: {args.text_file} ###")
    print(f"### Shard {args.shard_id+1}/{args.num_shard} ###")
    texts = [json.loads(l) for l in open(args.text_file, 'r')]
    shard_size = len(texts) // args.num_shard
    text_shard = texts[args.shard_id * shard_size : (args.shard_id+1) * shard_size]

    p_embs = []
    for i in tqdm(range(0, len(text_shard), 10000)):
        batch_texts = text_shard[i:i+10000]
        batch_p_emb = dpr.encoder_p.embed(batch_texts, batch_size=args.batch_size)
        batch_p_emb = batch_p_emb.cpu()
        p_embs.append(batch_p_emb)
    
    p_emb = torch.cat(p_embs, dim=0)
    print(p_emb.shape)
    print(f"### Save torch tensor to: {args.save_file} ###")
    torch.save(p_emb, args.save_file)
    