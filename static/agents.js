let editor;
let customNode;

window.addEventListener("load", () => {
    const container = document.getElementById("drawflow");
    editor = new Drawflow(container);
    editor.start();

    customNode = `
        <div class="custom-node">
        <input type="text" df-name placeholder="Enter text"/>
        </div>
    `;

    // Add node type
    editor.registerNode('custom', customNode);
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
    const data = editor.export();

    const response = fetch("/agent/save_workflow", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify(data)
                    });

}

const saveAgentBtn = document.getElementById("save-workflow-btn");

saveAgentBtn.addEventListener("click", saveAgentWorkflow);


const nodeDiv = document.querySelector('.agent-node-section');

nodeDiv.addEventListener('dragstart', (e) => {
    e.dataTransfer.setData('node-type', e.target.dataset.name);
});

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
        "custom",          // Name/type of node
        2,                 // Number of inputs
        2,                 // Number of outputs
        posX,              // x position
        posY,              // y position
        "custom",          // Data to store
        {},
        customNode
    );
});
