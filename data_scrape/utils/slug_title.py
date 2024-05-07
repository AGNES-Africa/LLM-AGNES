import os

def use_slug_as_title(directory, subfolders):
    
    for subfolder in subfolders:
        full_path = os.path.join(directory, subfolder)
        
        for filename in os.listdir(full_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(full_path, filename)
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                
                new_lines = []
                title_found = False
                modified_slug = None
                for line in lines:
                    if line.startswith('Title:') and line.strip() != 'Title: None':
                        title_found = True  # A valid title exists
                    
                    if line.startswith('Slug:') and not title_found:
                        slug = line.split('Slug:', 1)[1].strip()
                        modified_slug = slug.replace('-', ' ').split('.pdf')[0]  # Remove file extension and replace hyphens

                    new_lines.append(line)

                with open(file_path, 'w') as file:
                    for line in new_lines:
                        if line.strip() == 'Title: None' and modified_slug:
                            line = f'Title: {modified_slug}\n'