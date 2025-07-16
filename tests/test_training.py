import torch
import pytest
from torch.utils.data import Dataset
from egen.model.thl150 import THL150
from egen.model.config import ModelConfig
from egen.training.trainer import Trainer
from egen.training.config import TrainingConfig

class DummyDataset(Dataset):
    def __init__(self, vocab_size, seq_length, num_samples=4):
        self.vocab_size = vocab_size
        self.seq_length = seq_length
        self.num_samples = num_samples
    def __len__(self):
        return self.num_samples
    def __getitem__(self, idx):
        return {
            'input_ids': torch.randint(0, self.vocab_size, (self.seq_length,)),
            'labels': torch.randint(0, self.vocab_size, (self.seq_length,)),
        }

def test_trainer_single_batch_mixed_precision():
    config = ModelConfig(
        num_layers=2,
        hidden_size=16,
        intermediate_size=32,
        num_attention_heads=2,
        num_key_value_heads=2,
        max_position_embeddings=16,
        vocab_size=32,
    )
    model = THL150(config)
    dataset = DummyDataset(vocab_size=config.vocab_size, seq_length=4, num_samples=2)
    train_config = TrainingConfig(
        per_device_train_batch_size=2,
        num_train_epochs=1,
        use_mixed_precision=torch.cuda.is_available(),
        fp16=torch.cuda.is_available(),
        no_cuda=not torch.cuda.is_available(),
        distributed_training=False,
        dataloader_num_workers=0,
    )
    trainer = Trainer(model=model, train_dataset=dataset, config=train_config)
    result = trainer.train()
    assert isinstance(result, dict)
    assert 'loss' in result or 'train_loss' in result 