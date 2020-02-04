#!/bin/bash
#SBATCH --job-name=prepare_corpus
#SBATCH --output=prepare_corpus.out
#SBATCH --error=prepare_corpus.err
#SBATCH --cpus-per-task=20
#SBATCH --mem=100GB
#SBATCH -p short
#SBATCH --time=08:00:00

wd=/scratch/cheng.jial/pubmed
cd $wd
python prepare_corpus.py
