import argparse
import cv2
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torchvision
import torch.optim as optim
from torch.optim import lr_scheduler
from data_loader import get_loader
from models import VqaModel
import warnings

warnings.filterwarnings("ignore")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def load_str_list(fname):
    with open(fname) as f:
        lines = f.readlines()
    lines = [l.strip() for l in lines]
    return lines


qst_vocab = load_str_list("datasets/vocab_questions.txt")
ans_vocab = load_str_list("datasets/vocab_answers.txt")
word2idx_dict = {w: n_w for n_w, w in enumerate(qst_vocab)}
unk2idx = word2idx_dict['<unk>'] if '<unk>' in word2idx_dict else None
vocab_size = len(qst_vocab)


# def load_image(image_path, transform=None):
#     image = Image.open(image_path).convert('RGB')
#     image = image.resize([224, 224], Image.LANCZOS)
#
#     if transform is not None:
#         image = transform(image).unsqueeze(0)
#
#     return image


# def visualizeAttention(model, img, layer):
#     m = nn.Upsample(size=(224, 224), mode='bilinear')
#     pi = model.attn_features[layer].squeeze()
#     print(pi.size())
#     pi = pi.view(14, 14)
#     attn = m(pi)
#
#     image = image.squeeze(0)
#     img = torch.numpy(image)
#     attn = torch.numpy(attn)


def word2idx(w):
    if w in word2idx_dict:
        return word2idx_dict[w]
    elif unk2idx is not None:
        return unk2idx

    else:
        raise ValueError('word %s not in dictionary (while dictionary does not contain <unk>)' % w)


def main(args):
    image = cv2.imread(args.image_path)
    image = cv2.resize(image, dsize=(224, 224), interpolation=cv2.INTER_AREA)
    image = torch.from_numpy(image).float()
    image = image.to(device)
    image = image.unsqueeze(dim=0)
    image = image.view(1, 3, 224, 224)

    max_qst_length = 30

    question = args.question
    q_list = list(question.split(" "))

    idx = 'valid'
    qst2idc = np.array([word2idx('<pad>')] * max_qst_length)  # padded with '<pad>' in 'ans_vocab'
    qst2idc[:len(q_list)] = [word2idx(w) for w in q_list]

    question = qst2idc
    question = torch.from_numpy(question).long()

    question = question.to(device)
    question = question.unsqueeze(dim=0)

    # model = torch.load(args.saved_model)

    model = VqaModel(
        embed_size=1024,
        qst_vocab_size=len(qst_vocab),
        ans_vocab_size=len(ans_vocab),
        word_embed_size=300,
        num_layers=2,
        hidden_size=512
    )
    checkpoint = torch.load(args.saved_model)
    model.load_state_dict(checkpoint['state_dict'])

    model = model.to(device)

    model.eval()
    output = model(image, question)

    predicts = torch.softmax(output, 1)
    probs, indices = torch.topk(predicts, k=len(ans_vocab), dim=1)
    probs = probs.squeeze()
    indices = indices.squeeze()
    print("predicted - probabilty")
    for i in range(len(ans_vocab)):
        print("'{}' - {:.4f}".format(ans_vocab[indices[i].item()], probs[i].item()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_path', type=str, required=True)
    parser.add_argument('--question', type=str, required=True)
    parser.add_argument('--saved_model', type=str, required=True)

    args = parser.parse_args()
    main(args)