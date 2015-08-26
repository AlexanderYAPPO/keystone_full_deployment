Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 4096
    # vb.gui = true
  end

  config.vm.provision :ansible do |ansible|
    ansible.playbook = "ansible/deploy_keystone.yml"
    ansible.extra_vars = {
      global_os_user: "vagrant",
  }
  end

  config.vm.network :forwarded_port, guest: 5000, host: 5000 # forward keystone
end