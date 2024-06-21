import bpy
import math
import mathutils
import re
import random

class LSystem:
    def __init__(self, numIters, startStr, rules, step_length, default_angle, mesh_dict, random_seed=None):
        self.numIters = numIters
        self.startStr = startStr
        self.rules = rules
        self.step_length = step_length
        self.default_angle = default_angle
        self.resultStrs = [self.startStr]
        self.vertices = []
        self.edges = []
        self.faces = []
        self.vertex_index = 0
        self.mesh_objects = []
        self.mesh_dict = mesh_dict  # Dictionary to store mesh objects
        if random_seed is not None:
            random.seed(random_seed)  # Set seed for reproducibility
        else:
            random.seed()  # Re-seeds with current time or system state
        self.generate()


    def generate(self):
        oldStr = self.startStr
        for i in range(self.numIters):
            newStr = self.replaceProcess(oldStr)
            oldStr = newStr
            self.resultStrs.append(newStr)


    def replaceProcess(self, oldStr):
        return ''.join(self.replace(char) for char in oldStr)


    def replace(self, char):
        return self.rules.get(char, char)


    def extract_value(self, instruction):
        # Match both single values and ranges
        match = re.match(r'([A-Za-z\+\-\&\^<>\|])\(([\d\.]+)(?:,([\d\.]+))?\)', instruction)
        if match:
            symbol = match.group(1)
            if match.group(3):  # It's a range
                min_angle = float(match.group(2))
                max_angle = float(match.group(3))
                random_angle = random.uniform(min_angle, max_angle)
                return symbol, random_angle
            else:  # Single value
                return symbol, float(match.group(2))
        return instruction, None


    def create_sphere(self, location, diameter=0.5):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=diameter/2, location=location)
        sphere = bpy.context.object
        sphere.name = "StartingSphere"
        return sphere

    def create_edge_mesh(self, start, end):
        # Create a new mesh
        mesh_data = bpy.data.meshes.new("EdgeMesh")
        mesh_data.from_pydata([start, end], [(0, 1)], [])
        mesh_data.update()

        # Create an object with the mesh
        mesh_object = bpy.data.objects.new("EdgeObject", mesh_data)
        bpy.context.collection.objects.link(mesh_object)

        # Apply a skin modifier to the object
        mesh_object.modifiers.new(type='SKIN', name='SkinMod')
        # Adjust skin modifier properties as needed
        for vertex in mesh_object.data.skin_vertices[0].data:
            vertex.radius = [0.02, 0.02]  # Example radius, adjust as needed

        # Ensure the object is visible and selected
        bpy.context.view_layer.objects.active = mesh_object
        mesh_object.select_set(True)

        return mesh_object

    def draw(self):
        direction = mathutils.Vector([0, 1, 0])
        location = mathutils.Vector((0, 0, 0))
        stack = []

        # Create a sphere at the starting point
        self.create_sphere(location)

        for rule in self.resultStrs:
            index = 0
            while index < len(rule):
                instruction = rule[index]
                
                if index + 2 < len(rule) and rule[index + 1] == '(':
                    end_index = rule.find(')', index)
                    instruction = rule[index:end_index + 1]
                    index = end_index
                symbol, value = self.extract_value(instruction)

                if symbol in self.mesh_dict:
                    self.add_mesh_instance(symbol, location, direction)
                elif symbol == "F":
                    step = value if value is not None else self.step_length
                    new_location = location + direction * step
                    self.add_line(location, new_location)
                    location = new_location
                elif symbol == "f":
                    step = value if value is not None else self.step_length
                    location += direction * step
                elif symbol == "[":
                    stack.append((location.copy(), direction.copy()))
                elif symbol == "]":
                    location, direction = stack.pop()
                else:
                    self.rotate_direction(symbol, direction, value)
                index += 1

    def rotate_direction(self, symbol, direction, value):
        angle = math.radians(value if value is not None else self.default_angle)
        rotations = {
            "+": (0, 0, angle),
            "-": (0, 0, -angle),
            "&": (angle, 0, 0),
            "^": (-angle, 0, 0),
            "<": (0, angle, 0),
            ">": (0, -angle, 0),
            "|": (0, 0, math.pi)
        }
        if symbol in rotations:
            direction.rotate(mathutils.Euler(rotations[symbol], 'XYZ'))

    def add_line(self, start, end):
        # Create a mesh object for each edge
        self.create_edge_mesh(start, end)

    def add_mesh_instance(self, symbol, location, direction):
        mesh = self.mesh_dict[symbol]
        mesh_instance = mesh.copy()
        bpy.context.collection.objects.link(mesh_instance)
        mesh_instance.location = location

        # Generate random rotation
        random_rotation = mathutils.Euler((random.uniform(0, 2 * math.pi),
                                           random.uniform(0, 2 * math.pi),
                                           random.uniform(0, 2 * math.pi)), 'XYZ')
        mesh_instance.rotation_euler = random_rotation

#************************************
# main
#************************************
if __name__ == '__main__':
    numIters =  3  # Number of iterations to generate the structure
    step_length = 1
    default_angle = 30
    startStr = 'G'
    rules = {
        'G' : '[+FAG][-FAG][++FBG][--FBG]',
        'A' : '&F[&(90)F+(45)F]FFF',
        'B' : '^F[^(90)F+(45)F]FFF',

    }

    # Load predefined meshes and store them in a dictionary
    # Ensure you have objects named 'FlowerMesh' and 'LeafMesh' in your Blender scene
    try:
        core = bpy.data.objects['core']  # Replace with your mesh name
        leaf = bpy.data.objects['LeafMesh']  # Replace with your mesh name
    
    except KeyError as e:
        print(f"Error: {e}")
        core = None
        leaf = None

    mesh_dict = {
        'P': core,
        'L': leaf
    }

    # Create LSystem instance with random seed for reproducibility
    ls = LSystem(numIters, startStr, rules, step_length, default_angle, mesh_dict, random_seed=None)
    
    # Draw the LSystem
    ls.draw()
