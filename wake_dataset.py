import torch
from torch.utils.data import Dataset
import os
import pandas as pd

#create class that inherits abstract class Dataset
'''
Dataset needs to be able to access the /data/ folder, go into each case and load each component's wake image. It needs to be able to return an image based upon an input of dTdz and d0 (and which component?).

Ideally, don't read in all the images at once, and only load them in through the __getitem__ method 
'''

class WakeDataset(Dataset):
	'''Dataset to manage wake image data'''

	def __init__(self, root_dir, transform=None):
		self.root_dir = root_dir
		print("root dir: " + str(self.root_dir))
		print(os.listdir(self.root_dir))

		#get input variable combinations and store them in a list
		#input vars are read from the case directories
		input_combos = []
		for case in os.listdir(root_dir):
			if case.startswith('dTdz'):
				input_combos.append([float(case[4:9]), float(case[-3:])])

		self.length = len(input_combos)

		#turn input combos into a tensor
		self.input_combos_tensor = torch.FloatTensor(input_combos)
			
		self.frame = pd.DataFrame(input_combos)
		self.frame.columns = ['dTdz', 'depth']

		self.transform = transform

	def __len__(self):
		return self.length

	def __getitem__(self, index):

		item = self.input_combos_tensor[index]

		dTdz = item[0]
		depth = item[1]

		#return data in necessary format
		case_dir = '/%s/dTdz%0.3f_z%d' % (self.root_dir, dTdz, depth)
		uy_data = pd.read_csv(os.path.join(case_dir, 'Uy.csv'), header=None)
		#print(uy_data)		
		
		#trim data to 128x1024		
		uy_data = self.crop(uy_data, 1024)
		#print(uy_data)

		if self.transform:
			uy_data = self.crop(uy_data, 512)
			
		#convert output data to tensor
		uy_data_tensor = torch.FloatTensor(uy_data.values)
			
		#rescale output data to range (-1, 1)	
		y = self.rescale(uy_data_tensor, -1, 1)

		#rescale inputs 
		dTdz = self.rescale_by_value(dTdz, 'dTdz', -1, 1)
		depth = self.rescale_by_value(depth, 'depth', -1, 1)	
		
		x = torch.stack([dTdz, depth], 0)		

		return x.view(1, 1, 2), y.view(1, 128, len(uy_data.columns))
	
	def rescale(self, tensor, newMin, newMax): 	
		return newMin + (((tensor - torch.min(tensor)) * (newMax - newMin)) / (torch.max(tensor) - torch.min(tensor)))
		
	def rescale_by_value(self, val, col, newMin, newMax):
		return newMin + (((val - self.frame[col].min())) * (newMax - newMin)) / (self.frame[col].max() - self.frame[col].min())

	def crop(self, df, num):
		df.drop(df.columns[-(len(df.columns) - num):], axis=1, inplace=True)
		return df

