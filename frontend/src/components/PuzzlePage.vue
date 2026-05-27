<template>
  <div class="puzzle-container">
    <div class="puzzle-header">
      <h1>🧩 滑块拼图</h1>
      <el-button @click="goBack" type="primary">← 返回导航</el-button>
    </div>

    <div v-if="tiles.length > 0" class="puzzle-content">
      <div class="stats-bar">
        <div class="stat-item">
          <div class="stat-label">步数</div>
          <div class="stat-value">{{ moves }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">难度</div>
          <div class="stat-value">{{ size }}×{{ size }}</div>
        </div>
      </div>

      <div class="control-panel">
        <div class="control-row">
          <div class="control-group">
            <span class="control-label">难度系数</span>
            <el-button-group>
              <el-button 
                v-for="s in [3, 4, 5]" 
                :key="s"
                :type="size === s ? 'primary' : ''"
                @click="size = s"
              >
                {{ s }}×{{ s }}
              </el-button>
            </el-button-group>
          </div>

          <div class="control-group">
            <span class="control-label">游戏模式</span>
            <el-button-group>
              <el-button 
                :type="mode === 'number' ? 'primary' : ''"
                @click="mode = 'number'"
              >
                🔢 数字
              </el-button>
              <el-button 
                :type="mode === 'image' ? 'primary' : ''"
                @click="mode = 'image'"
              >
                🖼️ 图片
              </el-button>
            </el-button-group>
          </div>

          <div class="control-group">
            <el-button @click="resetGame" type="info">
              🔄 重置
            </el-button>
          </div>
        </div>

        <div v-if="mode === 'image'" class="control-row image-controls">
          <input 
            type="file" 
            ref="fileInputRef" 
            @change="handleImageUpload" 
            accept="image/*" 
            class="hidden-input" 
          />
          <el-button type="primary" @click="triggerUpload">
            📤 上传图片
          </el-button>
          <el-button @mousedown.native="showOriginal = true" @mouseup.native="showOriginal = false" @mouseleave.native="showOriginal = false">
            👁️ 按住预览
          </el-button>
        </div>
      </div>

      <div class="game-board" :style="{ gridTemplateColumns: `repeat(${size}, 1fr)` }">
        <div 
          v-if="showOriginal && mode === 'image'"
          class="original-preview"
          :style="{ backgroundImage: `url(${imageSrc})` }"
        ></div>

        <div 
          v-if="isSolved && moves > 0"
          class="victory-overlay"
        >
          <div class="victory-content">
            <div class="victory-icon">🏆</div>
            <h2>拼图完成！</h2>
            <p>共移动了 <strong>{{ moves }}</strong> 步</p>
            <el-button type="primary" size="large" @click="resetGame">
              再来一局
            </el-button>
          </div>
        </div>

        <div 
          v-for="originalVal in gridArray" 
          :key="originalVal"
          class="tile-wrapper"
          :style="getTileWrapperStyle(originalVal)"
          @click="handleTileClick(originalVal)"
        >
          <div 
            :class="getTileClasses(originalVal)"
            :style="getTileInnerStyle(originalVal)"
          >
            <template v-if="mode === 'number' && originalVal !== size * size - 1">
              {{ originalVal + 1 }}
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';

const emit = defineEmits(['back']);

const size = ref(3);
const mode = ref('number');
const imageSrc = ref('https://images.unsplash.com/photo-1506744626753-eba7bc10433f?q=80&w=800&auto=format&fit=crop');
const tiles = ref([]);
const isSolved = ref(false);
const moves = ref(0);
const showOriginal = ref(false);
const fileInputRef = ref(null);

const gridArray = computed(() => Array.from({ length: size.value * size.value }, (_, i) => i));

const isSolvedState = (tilesArray) => {
  return tilesArray.every((val, index) => val === index);
};

const shuffleTiles = (currentSize) => {
  let newTiles = Array.from({ length: currentSize * currentSize }, (_, i) => i);
  let emptyIdx = currentSize * currentSize - 1;
  let lastEmptyIdx = -1;
  const shuffleMoves = currentSize * currentSize * 50;

  for (let i = 0; i < shuffleMoves; i++) {
    const neighbors = [];
    const row = Math.floor(emptyIdx / currentSize);
    const col = emptyIdx % currentSize;

    if (row > 0) neighbors.push(emptyIdx - currentSize);
    if (row < currentSize - 1) neighbors.push(emptyIdx + currentSize);
    if (col > 0) neighbors.push(emptyIdx - 1);
    if (col < currentSize - 1) neighbors.push(emptyIdx + 1);

    const validNeighbors = neighbors.filter(n => n !== lastEmptyIdx);
    const candidates = validNeighbors.length > 0 ? validNeighbors : neighbors;
    const randomNeighbor = candidates[Math.floor(Math.random() * candidates.length)];

    [newTiles[emptyIdx], newTiles[randomNeighbor]] = [newTiles[randomNeighbor], newTiles[emptyIdx]];
    lastEmptyIdx = emptyIdx;
    emptyIdx = randomNeighbor;
  }

  if (isSolvedState(newTiles)) {
    return shuffleTiles(currentSize);
  }
  return newTiles;
};

const resetGame = () => {
  tiles.value = shuffleTiles(size.value);
  moves.value = 0;
  isSolved.value = false;
};

watch(size, () => {
  resetGame();
});

onMounted(() => {
  resetGame();
});

const handleTileClick = (originalVal) => {
  if (isSolved.value || originalVal === size.value * size.value - 1) return;

  const emptyOriginalVal = size.value * size.value - 1;
  const currentIndex = tiles.value.indexOf(originalVal);
  const emptyIndex = tiles.value.indexOf(emptyOriginalVal);

  const curRow = Math.floor(currentIndex / size.value);
  const curCol = currentIndex % size.value;
  const emptyRow = Math.floor(emptyIndex / size.value);
  const emptyCol = emptyIndex % size.value;

  const isAdjacent = Math.abs(curRow - emptyRow) + Math.abs(curCol - emptyCol) === 1;

  if (isAdjacent) {
    const newTiles = [...tiles.value];
    [newTiles[currentIndex], newTiles[emptyIndex]] = [newTiles[emptyIndex], newTiles[currentIndex]];
    tiles.value = newTiles;
    moves.value++;

    if (isSolvedState(newTiles)) {
      isSolved.value = true;
    }
  }
};

const triggerUpload = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
};

const handleImageUpload = (e) => {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (event) => {
      imageSrc.value = event.target.result;
      mode.value = 'image';
      resetGame();
    };
    reader.readAsDataURL(file);
  }
};

const getTileWrapperStyle = (originalVal) => {
  const currentIndex = tiles.value.indexOf(originalVal);
  if (currentIndex === -1) return { display: 'none' };

  const currentCol = currentIndex % size.value;
  const currentRow = Math.floor(currentIndex / size.value);
  const isEmpty = originalVal === size.value * size.value - 1;

  return {
    width: `${100 / size.value}%`,
    height: `${100 / size.value}%`,
    transform: `translate(${currentCol * 100}%, ${currentRow * 100}%)`,
    zIndex: isEmpty ? 0 : 10
  };
};

const getTileInnerStyle = (originalVal) => {
  if (mode.value !== 'image') return {};

  const origCol = originalVal % size.value;
  const origRow = Math.floor(originalVal / size.value);

  return {
    backgroundImage: `url(${imageSrc.value})`,
    backgroundSize: `${size.value * 100}% ${size.value * 100}%`,
    backgroundPosition: `${(origCol / (size.value - 1)) * 100}% ${(origRow / (size.value - 1)) * 100}%`
  };
};

const getTileClasses = (originalVal) => {
  const isEmpty = originalVal === size.value * size.value - 1;
  const isVisible = !isEmpty || isSolved.value;
  
  let classes = 'tile-inner ';
  
  if (!isVisible) {
    classes += 'tile-hidden ';
  } else {
    classes += 'tile-visible ';
  }

  if (mode.value === 'image') {
    classes += 'tile-image ';
  } else {
    classes += 'tile-number ';
  }

  if (!isEmpty && !isSolved.value) {
    classes += 'tile-clickable ';
  }

  return classes;
};

const goBack = () => {
  emit('back');
};
</script>

<style scoped>
.puzzle-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.puzzle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 30px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.puzzle-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.puzzle-content {
  max-width: 600px;
  margin: 0 auto;
}

.stats-bar {
  display: flex;
  justify-content: center;
  gap: 40px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.control-panel {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: space-between;
  margin-bottom: 15px;
}

.control-row:last-child {
  margin-bottom: 0;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-label {
  font-size: 12px;
  color: #909399;
  font-weight: 600;
  text-transform: uppercase;
}

.image-controls {
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.hidden-input {
  display: none;
}

.game-board {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  background: #E8E8E8;
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.original-preview {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  bottom: 12px;
  background-size: cover;
  background-position: center;
  border-radius: 8px;
  z-index: 20;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  transition: opacity 0.2s;
}

.victory-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  z-index: 30;
  backdrop-filter: blur(4px);
}

.victory-content {
  text-align: center;
  padding: 40px;
}

.victory-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.victory-content h2 {
  font-size: 36px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 10px 0;
}

.victory-content p {
  font-size: 18px;
  color: #606266;
  margin: 0 0 30px 0;
}

.victory-content strong {
  color: #409EFF;
  font-weight: bold;
}

.tile-wrapper {
  position: absolute;
  transition: all 0.2s ease-in-out;
  padding: 4px;
  box-sizing: border-box;
}

.tile-inner {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  transition: all 0.3s;
}

.tile-hidden {
  opacity: 0;
  transform: scale(0.95);
}

.tile-visible {
  opacity: 1;
  transform: scale(1);
}

.tile-image {
  background-size: cover;
  background-position: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tile-number {
  background: white;
  color: #303133;
  box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.1);
}

.tile-clickable {
  cursor: pointer;
}

.tile-clickable:hover {
  filter: brightness(1.05);
}

.tile-clickable:active {
  transform: scale(0.98);
}

@media (max-width: 640px) {
  .puzzle-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .control-row {
    flex-direction: column;
  }

  .control-group {
    width: 100%;
  }

  .control-group .el-button-group {
    width: 100%;
    display: flex;
  }

  .control-group .el-button-group .el-button {
    flex: 1;
  }
}
</style>
