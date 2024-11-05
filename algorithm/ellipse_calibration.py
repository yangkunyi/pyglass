import numpy as np
import py4DSTEM
from py4DSTEM import Probe

import matplotlib.pyplot as plt


# 1. 加载datacube数据
filepath_data = r"/home/jerry_zhou/pyglass/center_calibration/Diffraction SI.dm4"
datacube = py4DSTEM.import_file(
    filepath_data
)
# 生成探针模板（synthetic probe kernel）
def generate_synthetic_probe(radius, width, Qshape):
    """
    Creates a synthetic probe using a Gaussian function to approximate
    the probe's intensity distribution.
    """
    x = np.linspace(-radius, radius, Qshape[0])
    y = np.linspace(-radius, radius, Qshape[1])
    X, Y = np.meshgrid(x, y)
    
    # Gaussian function for synthetic probe
    sigma = width * radius
    probe = np.exp(- (X**2 + Y**2) / (2 * sigma**2))
    
    return probe
# 补的函数（自己生成的合成探针）	
probe_semiangle = 5.5  # 根据实验设置调整探针半角
probe = generate_synthetic_probe(
    radius=probe_semiangle,  # 探针的半径
    width=0.7,               # 探针宽度
    Qshape=datacube.Qshape   # datacube 的形状
)

# 设置布拉格盘检测参数
detect_params = {
    'corrPower': 1.0,
    'sigma': 0,
    'edgeBoundary': 4,
    'minRelativeIntensity': 0,
    'minAbsoluteIntensity': 200,
    'minPeakSpacing': 12,
    'subpixel': 'poly',
    'upsample_factor': 8,
    'maxNumPeaks': 1000,
    'CUDA': False  # 如果没有GPU支持，将CUDA设置为False
}

# 使用探针模板进行布拉格盘检测，生成初始BVM
#bragg_peaks = datacube.find_Bragg_disks(template=probe.kernel, **detect_params)
bragg_peaks = datacube.find_Bragg_disks(template=probe, **detect_params) #根据补的函数 没用到源库kernel属性
bragg_vector_map_centered = bragg_peaks.get_bvm()

# 2. 定义拟合椭圆模型函数
def fit_ellipse_intensity(qx, qy, intensity):
    from scipy.optimize import curve_fit

    def ellipse_intensity_model(coords, I_r, q_0, A, B, C, s, I_0, I_1):
        qx, qy = coords
        return (I_r * np.exp(-((q_0 - np.sqrt(A * qx**2 + B * qx * qy + C * qy**2))**2) / (2 * s**2))
                + I_0 + I_1 * np.sqrt(qx**2 + qy**2))

    # 提供初始猜测值
    popt, _ = curve_fit(ellipse_intensity_model, (qx, qy), intensity, p0=[1, 1, 1, 1, 1, 1, 0, 0])
    I_r, q_0, A, B, C, s, I_0, I_1 = popt
    return A, B, C  # 返回椭圆拟合参数

# 从BVM中提取(qx, qy)坐标和强度数据进行拟合
qx, qy = np.meshgrid(np.arange(bragg_vector_map_centered.shape[0]), 
                     np.arange(bragg_vector_map_centered.shape[1]), indexing='ij')
intensity = bragg_vector_map_centered.data.ravel()  # 将强度数据展平为一维数组
A, B, C = fit_ellipse_intensity(qx.ravel(), qy.ravel(), intensity)  # 获取椭圆系数

# 3. 应用坐标变换以校正椭圆形失真
def apply_ellipse_correction(qx, qy, A, B, C):
    """
    使用矩阵变换将 (qx, qy) 从椭圆变换为圆形坐标。
    """
    M_ellipse = np.array([[A, B / 2],
                          [B / 2, C]])

    # 计算特征值和特征向量
    eigvals, eigvecs = np.linalg.eigh(M_ellipse)
    D = np.diag(np.sqrt(eigvals))  # 对角化并取特征值的平方根

    # 计算校正矩阵
    correction_matrix = eigvecs @ D @ eigvecs.T


    # 扁平化 qx 和 qy，然后应用校正矩阵
    q_coords = np.vstack([qx.ravel(), qy.ravel()])  # 形状 (2, N)
    corrected_coords = np.linalg.inv(correction_matrix) @ q_coords  # 形状 (2, N)

    # 将校正后的坐标调整为原来的形状
    qx_corrected = corrected_coords[0].reshape(qx.shape)
    qy_corrected = corrected_coords[1].reshape(qy.shape)

    return qx_corrected, qy_corrected, correction_matrix

# 应用校正，生成校正后的BVM
qx_corrected, qy_corrected, correction_matrix = apply_ellipse_correction(qx, qy, A, B, C)

print(f"A: {A}, B: {B}, C: {C}")
print("Correction matrix:\n", correction_matrix)
print("Corrected qx range:", qx_corrected.min(), qx_corrected.max())                   #
print("Corrected qy range:", qy_corrected.min(), qy_corrected.max())                   #



# 检查坐标点是否有效
out_of_bounds_count = 0                                                                #


# 手动指定形状来生成二维数组
bragg_vector_map_centered_corrected = np.zeros((256, 256))
for i in range(bragg_vector_map_centered.shape[0]):
    for j in range(bragg_vector_map_centered.shape[1]):
        corrected_i, corrected_j = int(round(qx_corrected[i, j])), int(round(qy_corrected[i, j]))
        if (0 <= corrected_i < bragg_vector_map_centered.shape[0] and 0 <= corrected_j < bragg_vector_map_centered.shape[1]):
            bragg_vector_map_centered_corrected[corrected_i, corrected_j] = bragg_vector_map_centered[i, j]
        else:                                                                       #
            out_of_bounds_count += 1                                                    #

print("Number of out-of-bounds points:", out_of_bounds_count)                           #

# 将 bragg_vector_map_centered 转换为 NumPy 数组
bvm_data = np.array(bragg_vector_map_centered.data)  # 替换 `data` 为适合的属性名称
# 打印最小值和最大值
print("Original BVM min:", bvm_data.min())
print("Original BVM max:", bvm_data.max())





# 4. 可视化校正后的BVM
# 归一化处理
bragg_vector_map_centered_corrected = (
    bragg_vector_map_centered_corrected - np.min(bragg_vector_map_centered_corrected)
) / (
    np.max(bragg_vector_map_centered_corrected) - np.min(bragg_vector_map_centered_corrected)
)

# 可视化校正后的BVM
py4DSTEM.visualize.show(
    bragg_vector_map_centered_corrected,
    figsize=(4, 4)
)


# 5. 保存校正后的BVM图像
plt.imshow(bragg_vector_map_centered_corrected, cmap='gray', vmin=0, vmax=np.percentile(bragg_vector_map_centered_corrected, 99))
plt.colorbar()
plt.savefig("corrected_BVM.png")
plt.show()

