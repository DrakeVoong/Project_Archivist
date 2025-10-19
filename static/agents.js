let editor;
let customNode;
let node_list;

async function registerNodeList() {
    const response = await fetch("/agent/get_node_list");
    const nodes = await response.json();

    node_list = {};

    for (const node_name in nodes){
        const node_data = nodes[node_name];

        // Add inner node html
        let customNode_html = '<div class="custom-node">';
        customNode_html += `<div>${node_data.name}</div>`;
        
        // Add user input fields
        const settings = node_data.settings;
        settings_count = Object.keys(settings).length;
        let count = 1;
        for (const setting_name in settings){
            const setting_type = settings[setting_name];
            customNode_html += `<input type="text" df-setting_${count} placeholder="${setting_type}"/>`;
            count++;
        }
        customNode_html += '</div>';
        
        nodes[node_name].html = customNode_html;
        editor.registerNode(node_name, customNode_html);
    }

    node_list = nodes;
}

window.addEventListener("load", async () => {
    const container = document.getElementById("drawflow");
    editor = new Drawflow(container);
    editor.start();
    
    await registerNodeList();

    // Add to node list
    const agent_node_list = document.getElementById("agent-node-list");

    for (const node in node_list) {
        const node_section_div = document.createElement("div");
        node_section_div.classList.add("agent-node-section");
        node_section_div.draggable = "true";
        node_section_div.dataset.name = node;
        node_section_div.textContent = node;

        node_section_div.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('node-type', e.target.dataset.name);
        });

        agent_node_list.appendChild(node_section_div);
    }
})

// New agent
document.getElementById("new-agent-btn").addEventListener("click", async () => {
    
    const newAgentModal = document.getElementById("new-agent-name-modal");
    const agentName = newAgentModal.querySelector("#new-agent-name");

    agentName.value = "";
    newAgentModal.style.display = "block";
});

document.getElementById("confirm-new-agent").addEventListener("click", async () => {
    const newAgentModal = document.getElementById("new-agent-name-modal");
    const agentName = newAgentModal.querySelector("#new-agent-name");

    newAgentModal.style.display = "none";

    const response = await fetch("/agent/new_workflow", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({"name": agentName.value}) 
                    });

    const data = await response.json();
    
    const drawflowEditor = document.getElementById("drawflow");
    editor.clear();
    drawflowEditor.dataset.agent_name = agentName;
    drawflowEditor.dataset.agent_id = data.id;
})

document.getElementById("state-workflow-check").addEventListener("change", async () => {
    const drawflowEditor = document.getElementById("drawflow");
    const agentName = drawflowEditor.dataset.agent_name;
    const agentId = drawflowEditor.dataset.agent_id;

    const response = await fetch("/agent/add_workflow_to_events", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({"name": agentName, "id": agentId}) 
                    });

    const data = await response.json();

    if (data.status != "200") {
        this.checked = false;
    }

})

async function loadAgentList() {
    const response = await fetch("/agent/get_agent_list");
    const data = await response.json();

    const agentList = document.getElementById("agent-list");
    agentList.innerHTML = "";
    for (const agent of data) {
        const agentDiv = document.createElement("div");
        agentDiv.classList.add("agent-list-section");
        agentDiv.textContent = agent;
        agentDiv.dataset.name = agent;
        agentDiv.role = "button";

        agentDiv.addEventListener("click", () => {
            loadAgentWorkflow(agentDiv.dataset.name);
        });

        agentList.appendChild(agentDiv);
    }

}

window.addEventListener("load", () => {
    loadAgentList();
});

async function loadAgentWorkflow(agentName) {
    const response = await fetch(`/agent/load_agent_workflow/${agentName}`);
    const data = await response.json();

    editor.import(data);
}

async function saveAgentWorkflow() {
    const workflow = editor.export();

    const response = fetch("/agent/save_workflow", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify(workflow)
                    });

}

const saveAgentBtn = document.getElementById("save-workflow-btn");
saveAgentBtn.addEventListener("click", saveAgentWorkflow);

// Refactoring to be at an ON/OFF state instead of activating

// async function runAgentWorkflow() {
//     const workflow = editor.export();

//     const response = await fetch("/agent/run_agent_workflow", {
//                         method: "POST",
//                         headers: {"Content-Type": "application/json"},
//                         body: JSON.stringify(workflow)
//                     });

//     const data = await response.json();

//     console.log(data);
// }

// const runAgentBtn = document.getElementById("run-workflow-btn");
// runAgentBtn.addEventListener("click", runAgentWorkflow);

const editorContainer = document.getElementById('drawflow');

// Allow drop
editorContainer.addEventListener('dragover', (e) => {
    e.preventDefault();
});

// Handle drop
editorContainer.addEventListener('drop', (e) => {
    e.preventDefault();
    
    // Get node type
    const nodeType = e.dataTransfer.getData('node-type');
    
    // Get drop position relative to editor
    const rect = editorContainer.getBoundingClientRect();
    const posX = e.clientX - rect.left;
    const posY = e.clientY - rect.top;

    // Add node to Drawflow
    editor.addNode(
        nodeType,          // Name/type of node
        Object.keys(node_list[nodeType].inputs).length,
        Object.keys(node_list[nodeType].outputs).length,
        posX,              // x position
        posY,              // y position
        "custom", // class
        structuredClone(node_list[nodeType]), // data
        node_list[nodeType].html //html
    );
});

// Check if node connections are valid types
// TODO: Fix on_message output_1 not connecting with print_string input_1
window.addEventListener("load", () => {
    editor.on('connectionCreated', (connection) => {
        // connection object contains: { output_id, input_id, output_class, input_class }
        
        // 1. Get the HTML elements for the connected ports
        const outputElement = document.querySelector(`#node-${connection.output_id}`);
        const inputElement = document.querySelector(`#node-${connection.input_id}`);

        const output_node = editor.getNodeFromId(connection.output_id);
        const input_node = editor.getNodeFromId(connection.input_id);

        const output_data = output_node.data;
        const input_data = input_node.data;

        let found_match = false;
        
        let output_port_num;
        let input_port_num;
        
        /*
        Find the input and output used in connection.
        */
       const output_port = output_node.outputs;
       // Loop thru all output port
       for (const output_num in output_port) {
           if (found_match) {
               break;
            }
            const connections = output_port[output_num].connections;
            // Loop thru all connections of an output port
            for (const node_connection_num in connections) {
                const node_connection = connections[node_connection_num];
                // Check if the connection was the newly created connection
                if (node_connection.node == connection.input_id) {
                    output_port_num = output_num.split("_")[1];
                    input_port_num = node_connection.output.split("_")[1];
                    
                    
                    found_match = true;
                    break;
                }
            }
        }
        
        // Check if the input and output of the connection are the same type
        output_port_num = parseInt(output_port_num)-1;
        input_port_num = parseInt(input_port_num)-1;

        const valid_outputs_array = Object.values(output_data.outputs);
        const valid_inputs_array = Object.values(input_data.inputs);

        if (valid_outputs_array[output_port_num] == valid_inputs_array[input_port_num]) {
            console.log("Valid connection");
        } else {
            console.log(`Invalid connection`);
            editor.removeSingleConnection(connection.output_id, connection.input_id, connection.output_class, connection.input_class);
        }
        
    });
});


// Add type hint on input and output port
window.addEventListener("load", () => {
    editor.on('nodeCreated', (id) => {
        const new_node = document.querySelector(`#node-${id}`)
        const node_data = editor.getNodeFromId(id).data;
                
        // Add input port type hint
        let input_count = 1;
        const input_div = new_node.querySelector(`.inputs`);
        const node_inputs = node_data.inputs;
        for (const input in node_inputs) {
            console.log(input)
            const input_div_num = input_div.querySelector(`.input_${input_count}`);
            input_div_num.innerHTML = `<div class="input-type">${input}(${node_inputs[input]})</div>`;
            input_count++;
        }

        // Add output port type hint
        output_count = 1;
        const output_div = new_node.querySelector(`.outputs`);
        const node_outputs = node_data.outputs;
        for (const output in node_outputs) {
            const output_div_num = output_div.querySelector(`.output_${output_count}`);
            output_div_num.innerHTML = `<div class="output-type">${output}(${node_outputs[output]})</div>`;
            output_count++;
        }

        
        // Add margin for inner node html, so port text does not overlap with inner node html
        const maxPort = Math.max(input_count, output_count);
        let offset = 20*maxPort;
        if (maxPort > 1) {
            offset += (maxPort/2)* 5;
        }
        
        const node_html = new_node.querySelector(".drawflow_content_node");
        node_html.style.marginTop = `${offset}px`;


        // // Change dataset.setting_n in input fields
        // const inner_node_html = node_html.querySelector(".custom-node");
        // const inputs = inner_node_html.querySelectorAll("input");

        // let count = 1;
        // for (const input of inputs) {
        //     console.log(input)
        //     delete input.dataset[`setting_${count}`]
        //     input.dataset[`setting_${id}_${count}`]
        //     count++;
        // }


    })
});