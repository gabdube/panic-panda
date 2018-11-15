source /home/gdube/Documents/other/VulkanSDK/1.0.68.0/setup-env.sh

glslangValidator -V ./main/main.vert -o ./main/main.vert.spv
glslangValidator -V ./main/main.frag -o ./main/main.frag.spv
