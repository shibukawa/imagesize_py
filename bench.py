import timeit
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import imagesize

imagepath = os.path.join(os.path.dirname(__file__), "test", "images", "test.png")

try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except ImportError:
        Image = None

def get_by_pil(filepath):
    img = Image.open(filepath)
    (width, height) = img.size
    return width, height

def bench_purepython():
    imagesize.get(imagepath)

def bench_pil():
    get_by_pil(imagepath)

def bench():
    print("pure python png")
    print(timeit.timeit('bench_purepython()', number=100000, setup="from __main__ import bench_purepython"))
    print("pil png")
    print(timeit.timeit('bench_pil()', number=100000, setup="from __main__ import bench_pil"))

if __name__ == "__main__":
    bench()
