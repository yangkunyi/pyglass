# PyGlass


### Setup

#### Conda

``` bash
cd pyglass
conda env create -f pyglass_backend.yaml
```
#### Quasar

https://quasar.dev/start/quick-start/

### Run

#### Backend

``` bash
cd backend
conda activate pyglass_backend
python flask_test.py
```

#### Frontend

``` bash
cd frontend
quasar dev -m electron
```

### Build
#### Backend
``` bash
cd backend
conda activate pyglass_backend
pyinstaller --noconfirm --onedir --console  "flask_test.py"
```
一些额外的库和文件需要被加入到打包后的`_internal`中。包括
```
abtem
pyxem
pyxem-0.20.0.dist-info
diffpy
distributed
hyperspy
pymatgen
```
`kirkland.pkl`需要放在根目录文件夹下。

```
-- output
    -- _internal
    -- flask_test.exe
    -- kirkland.pkl
```